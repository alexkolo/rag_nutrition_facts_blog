"""
Start app: `streamlit run app.py`
View in browser: `http://localhost:8501`
"""

import os
import uuid
import warnings
from collections.abc import Iterable
from datetime import datetime
from pathlib import Path
from typing import Any

import pytz
import streamlit as st
from dotenv import load_dotenv
from lancedb.table import Table as KBaseTable

import src.constants as cst
from src.app_utils import connect_to_llm, init_st_keys
from src.app_widgets import create_button, create_chat_msg, create_first_assistant_msg, show_chat_history, show_md_file
from src.llm_api import build_full_llm_chat_input, stream_chat_response
from src.mongodb import MongodbClient, get_mongodb_config, save_chat_history
from src.prompt_building import WELCOME_MSG, extract_context_from_msg
from src.retrieval import connect_to_lancedb_table

# ignore future warnings
warnings.simplefilter(action="ignore", category=FutureWarning)


# Chat Parameters
# -----------------------------
chat_config: dict[str, Any] = cst.get_rag_config()["chat"]
BOT_AVATAR: str = chat_config["bot_avatar"]
AVATARS: dict[str, Any] = {"assistant": BOT_AVATAR, "user": chat_config["user_avatar"]}
STREAM_DEFAULT: bool = chat_config["stream_default"]
CHAT_HISTORY_HEIGHT: int = chat_config["chat_history_height"]
SHOW_HAL_WARNING: int = 2  # after 1 user question show hallucination warning
HAL_WARNING_MSG: str = (
    "Please note that with the current state of technology, the digital assistant may hallucinate! 🙃"
)
ASK_USER_FEEDBACK: int = 2  # after 1 user questions ask user feedback

APP_INTRO_TEXT: str = """ """

# App Header
APP_TITLE = f"Nutrify Your Life {BOT_AVATAR}"
APP_SUBTITLE = "A Science-Based Health & Lifestyle Companion"
APP_INTRO_TEXT: str = """
"Nutrify Your Life" is your personal companion, inspired by the science-based expertise of
[NutritionFacts.org](https://nutritionfacts.org/about/). Designed to answer your questions about healthy eating and
lifestyle choices, this AI-powered digital assistant draws from over 1,200 well-researched blog posts since 2011.
Whether you're looking for nutrition tips or guidance on living a healthier life, it offers reliable, science-backed
insights to help you live a healthier, more informed life.
"""

# response time threshold to show info
RESP_TIME_THRESHOLD: int = 4  # in seconds
SLOW_RESP_TIME_INFO: str = """
_Response time may be a bit slow as the app uses a **free tier** for its LMM API provider
[Groq Cloud](https://groq.com/) to make it **accessible to everyone**.
Sorry for the inconvenience._
"""

# LLM Parameters
# -----------------------------
llm_config: dict[str, Any] = cst.get_rag_config()["llm"]
LLM_TEMP: float = llm_config["settings"]["model_temp"]
LLM_API_NAME: str = llm_config["settings"]["api_name"]
LLM_API_CONFIG: dict[str, Any] = llm_config["api"][LLM_API_NAME]
LLM_API_KEY_NAME: str = LLM_API_CONFIG["key_name"].upper()
LLM_API_KEY_URL: str = LLM_API_CONFIG["key_url"]
TOTAL_MAX_TOKEN: int = LLM_API_CONFIG["token"]["total_max"]

# get the config for the retriever
retriever_config: dict = cst.get_rag_config()["retriever"]


# Chat Bot Elements
# -----------------------------


def process_user_input(
    user_prompt: str,
    avatars: dict[str, Any],
    api_name: str,
    k_base: KBaseTable,
    stream: bool = STREAM_DEFAULT,
):
    if stream is False:
        # error handling
        raise ValueError("Stream=False is not supported in this version of the app")

    # show user message in the chat history
    create_chat_msg(content=user_prompt, role="user", avatar=avatars["user"])

    # create assistant response
    with st.chat_message("assistant", avatar=avatars["assistant"]):
        with st.spinner("I'm thinking..."):
            # build LLM chat input
            # TODO: check when message gets too big
            chat_history: list[dict[str, str]] = st.session_state["messages"]
            messages: list[dict[str, str]] = build_full_llm_chat_input(
                user_prompt=user_prompt,
                chat_history=chat_history,
                k_base=k_base,
                retriever_config=retriever_config,
            )
            # save first message, which contains context
            st.session_state["retrieval"].append(extract_context_from_msg(messages[0]["content"]))

            # send message to LLM and get response
            t_start = datetime.now()
            client = st.session_state["llm_client"]
            streamed_response_raw: Iterable = client.chat.completions.create(
                model=st.session_state["model_name"],
                messages=messages,
                temperature=st.session_state["model_temp"],
                stream=stream,
                # max_tokens=RESPONSE_MAX_TOKENS,
            )
            t_duration = datetime.now() - t_start

        # copy value, since `stream_chat_response` modifies it
        n_tokens_before: int = int(st.session_state["total_tokens"])
        streamed_response_str: Iterable[str] = stream_chat_response(streamed_response_raw, api_name=api_name)
        n_tokens_delta: int = st.session_state["total_tokens"] - n_tokens_before
        full_response: str = st.write_stream(streamed_response_str)
    # Add assistant response to chat history
    st.session_state["messages"].append(
        {
            "role": "assistant",
            "content": full_response,
            "response_time": t_duration.total_seconds(),
            "token_delta": n_tokens_delta,
            "llm_usage": st.session_state["llm_usage"],
        }
    )


# Secrets
# -----------------------------
ST_SECRETS_FILE: str = ".streamlit/secrets.toml"
init_st_keys("deployed")
if st.session_state["deployed"] is None:
    st.session_state["deployed"] = st.secrets.get("deployed", False) if Path(ST_SECRETS_FILE).exists() else False

# API KEY of LLM Provider
# ``````````````````````````
init_st_keys(LLM_API_KEY_NAME, "")
if st.session_state[LLM_API_KEY_NAME] == "":
    LLM_API_KEY_VALUE: str = ""
    # 1. see in streamlit secrets, if available
    if Path(ST_SECRETS_FILE).exists():
        LLM_API_KEY_VALUE = st.secrets.get(LLM_API_KEY_NAME, "")
    # 2. see in .env, if available
    if LLM_API_KEY_VALUE == "":
        load_dotenv()
        LLM_API_KEY_VALUE = os.getenv(LLM_API_KEY_NAME, "")

    st.session_state[LLM_API_KEY_NAME] = LLM_API_KEY_VALUE

if st.session_state[LLM_API_KEY_NAME]:
    api_key_input_label = f"You have the option to enter an [API KEY of the LLM provider **{LLM_API_NAME.capitalize()}**]({LLM_API_KEY_URL}), which is **for free**!  \n_Otherwise, the app creator's API KEY is used, which may slow down response time because it uses a free tier._"
    api_key_input_placeholder = "Optional: enter an API KEY here"
else:
    api_key_input_label = f"You have to enter an [API KEY of the LLM provider **{LLM_API_NAME.capitalize()}**]({LLM_API_KEY_URL}), which is **for free**, to use this app!"
    api_key_input_placeholder = "Enter an API KEY here"

# Initialize chat history
# -----------------------------
init_st_keys("messages", [])
init_st_keys("submit_button", False)
init_st_keys("start_chat", False)
init_st_keys("total_tokens", 0)
init_st_keys("llm_usage", {})
init_st_keys("n_sessions", 1)
init_st_keys("user_info", cst.USER_INFO_TEMPLATE)
init_st_keys("model_temp", LLM_TEMP)
init_st_keys("model_name")
init_st_keys("retrieval", [])
init_st_keys("rsp_time_info", False)
init_st_keys("own_api_key", False)

# Page starts here
# ==========================
st.set_page_config(page_title=APP_TITLE, page_icon=BOT_AVATAR)

# Header
# ------------
st.header(f"{BOT_AVATAR} {APP_TITLE}", divider=False)
st.subheader(APP_SUBTITLE, divider="blue")
if not st.session_state["start_chat"]:
    st.info(APP_INTRO_TEXT, icon="💡")

# Connect to Knowledge Base
# ------------
init_st_keys("kbase_loaded", False)
try:
    k_base: KBaseTable = connect_to_lancedb_table(**cst.get_rag_config()["knowledge_base"])
    # test connection
    if not st.session_state["kbase_loaded"]:
        n_entries = k_base.count_rows()
        st.session_state["kbase_loaded"] = True
        # st.success(f"Connected to knowledge database. Found {n_entries} entries.", icon="✅")
except Exception as error:
    st.error("Connection to knowledge database failed!", icon="❌")
    # show traceback
    raise error


# Connect to User Database
# ------------
init_st_keys("mongodb_connected", False)
with st.spinner("Connecting to user database..."):
    mongodb_client = MongodbClient(**get_mongodb_config(deployed=st.session_state["deployed"]))
if not mongodb_client.connection_test():
    st.error("Connection to user database failed!", icon="❌")
else:
    st.session_state["mongodb_connected"] = True

# Check LLM API Key
# ------------


# User-Name Container
# ------------
with st.expander(label="👤 User info", expanded=not st.session_state["start_chat"]):
    with st.form(key="user_form", border=False):
        # st.subheader("Who are you?")
        # User's name (required)
        user_name: str = st.text_input(
            label="Before you can start the chat, please tell me your name:", placeholder="Sam Altman", key="user_name"
        )

        # LLM API KEY
        user_llm_key: str = st.text_input(
            label=api_key_input_label, placeholder=api_key_input_placeholder, type="password", key="user_llm_key"
        )

        # Submit button
        submit_button = st.form_submit_button(label="Save & continue", disabled=st.session_state["start_chat"])
        if submit_button:
            st.session_state["submit_button"] = True
            st.session_state["user_info"].update(
                {
                    "user_id": str(uuid.uuid4()),
                    "timestamp": datetime.now(tz=pytz.utc).strftime("%Y-%m-%d %H:%M:%S"),
                    "user_name": user_name,
                }
            )
            if user_name:
                with st.spinner("Saving your information..."):
                    if st.session_state["mongodb_connected"]:
                        mongodb_client.insert_one(st.session_state["user_info"])
                st.success(
                    f"Hi **{user_name}**. Thank you for your information! Next step: Wake up the digital assistant!",
                    icon="✅",
                )

            if not user_name:
                st.info("Please provide your name to use the digital assistant.", icon="👆")

            if user_llm_key:
                st.session_state[LLM_API_KEY_NAME] = user_llm_key  # overwrite key of app creator
                st.success("Also thank you for using your own API KEY!", icon="💚")
                st.session_state["own_api_key"] = True
            else:
                st.session_state["own_api_key"] = False
            if not st.session_state[LLM_API_KEY_NAME]:
                st.error(
                    f"The [API KEY of the LLM provider **{LLM_API_NAME.capitalize()}**]({LLM_API_KEY_URL}) is missing!",
                    icon="❌",
                )

# Chat-Control Container
# ------------
user_name = st.session_state["user_info"]["user_name"]
if st.session_state["submit_button"] and user_name and st.session_state[LLM_API_KEY_NAME]:
    # -------
    with st.container(border=False):
        st.subheader("Start chatting")
        with st.popover(
            "⚖ :red[**Please read this disclaimer before engaging with the digital assistant:**]",
            use_container_width=True,
        ):
            # inspired by: https://cloud.docs.tamr.com/page/ai-chatbot-disclaimer
            # https://wow.groq.com/privacy-policy/
            show_md_file(cst.BOT_DISCLAIMER)

        left_button, middle_button, right_button = st.columns(3, vertical_alignment="center")
        with left_button:
            start_chat = create_button(
                "start_chat",
                "Wake up the digital assistant ⏰",
                default=False,
                type="primary",
                disabled=st.session_state["start_chat"],
                use_container_width=True,
            )
        with middle_button:
            reset_chat = st.button(
                "Reset Chat History 🚮",
                on_click=st.session_state["messages"].clear,
                disabled=not st.session_state["start_chat"],
                use_container_width=True,
            )
            if reset_chat:
                st.session_state["n_sessions"] += 1
        with right_button:
            st.button(
                "Reset All 🧹",
                on_click=st.session_state.clear,
                disabled=not st.session_state["start_chat"],
                use_container_width=True,
            )


# Chat-Box Container
# ------------
if st.session_state["start_chat"]:
    new_chat: bool = not st.session_state["messages"]
    with st.container(border=False):
        # chat history
        chat_window = st.container(border=True, height=250 if new_chat else CHAT_HISTORY_HEIGHT)
        with chat_window:
            if reset_chat is True:
                st.success("Chat history has been reset.", icon="🗑️")

            # waking up assistant, if needed
            connect_to_llm(
                api_key=st.session_state[LLM_API_KEY_NAME],
                api_name=LLM_API_NAME,
                api_config=LLM_API_CONFIG,
                user_provided_key=st.session_state["own_api_key"],
            )

            if new_chat:
                # show 1st assistant message in the chat history
                create_first_assistant_msg(
                    msg=WELCOME_MSG.format(user_name=user_name),
                    avatar=BOT_AVATAR,
                    stream=STREAM_DEFAULT,
                )
            else:
                # show chat message history
                show_chat_history(avatars=AVATARS)

        # User input widget (at the bottom, outside of the chat history)
        user_prompt = st.chat_input(
            placeholder="Ask your question here, e.g. 'Is Wi-Fi dangerous?', 'Is a microwave dangerous?', 'How to eat healthy?'",
            key="user_input",
            max_chars=500,
            disabled=not st.session_state["start_chat"] or st.session_state["total_tokens"] >= TOTAL_MAX_TOKEN,
        )

        if user_prompt:
            with chat_window:  # show everything below in the chat history
                t_start = datetime.now()
                process_user_input(user_prompt, avatars=AVATARS, api_name=LLM_API_NAME, k_base=k_base)
                t_duration = datetime.now() - t_start
                if t_duration.total_seconds() > RESP_TIME_THRESHOLD and not st.session_state["own_api_key"]:
                    st.info(SLOW_RESP_TIME_INFO, icon="⏳")

            # save chat history
            if st.session_state["mongodb_connected"]:
                save_chat_history(
                    mongodb_client,
                    user_id=st.session_state["user_info"]["user_id"],
                    n_sessions=st.session_state["n_sessions"],
                    chat_history=st.session_state["messages"],
                    retrieval=st.session_state["retrieval"],
                )

        with chat_window:
            if st.session_state["total_tokens"] >= TOTAL_MAX_TOKEN:
                st.error("Chat history is too long. Please reset it.", icon="🚫")

    # show warning
    # ----------------------
    if len(st.session_state["messages"]) > SHOW_HAL_WARNING:
        st.warning(HAL_WARNING_MSG)

    # Ask for user feedback
    # ----------------------
    if len(st.session_state["messages"]) > ASK_USER_FEEDBACK:
        init_st_keys("user_rating")
        fb_disabled: bool = st.session_state["user_rating"] is not None

        fb_options: list[str] = ["🤮", "😕", "😐", "😀", "😍"]
        with st.form(key="feedback_form", border=True):
            user_fb = st.radio(
                label="**Please let me know how helpful you find this digital assistant:**",
                options=fb_options,
                index=st.session_state.get("user_rating", len(fb_options) - 1),
                disabled=fb_disabled,
                horizontal=True,
            )
            submit = st.form_submit_button("Submit", type="primary", use_container_width=True, disabled=fb_disabled)

        # save feedback
        if submit:
            value: int = fb_options.index(user_fb)
            user_likes_bot: bool = user_fb in ["😀", "😍"]

            st.session_state["user_rating"] = value
            if user_likes_bot:
                st.balloons()
            with st.spinner("Saving your feedback..."):
                if st.session_state["mongodb_connected"]:
                    mongodb_client.update_single_field(
                        filter={"user_id": st.session_state["user_info"]["user_id"]},
                        field="like_bot",
                        value=value,
                    )
            st.success(f"Thank you, **{user_name}**, for your feedback!", icon="💚" if user_likes_bot else "🙏")

# Debug
# ==============
st.write("###")
with st.expander("`Technical Details`", expanded=False):
    st.write(f"`LLM used: '{st.session_state['model_name'] or 'not yet defined'}'`")
    st.write(
        f"`{st.session_state['total_tokens']/TOTAL_MAX_TOKEN:.0%}"
        " of conversation capacity used before a chat history reset is required.`"
    )

if not st.session_state["deployed"]:
    with st.expander("🤓 _Debug Information_", expanded=False):
        st.button("Reset All 🧹", on_click=st.session_state.clear)
        st.write("Session State:")
        session_state: dict = dict(st.session_state)
        # del session_state[LLM_API_KEY_NAME]
        st.json(session_state, expanded=False)

        # show env. variables
        st.write("Environment Variables:")
        st.json(dict(os.environ), expanded=False)
