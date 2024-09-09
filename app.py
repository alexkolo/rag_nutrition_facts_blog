"""
Start app: `streamlit run app.py`
View in browser: `http://localhost:8501`
"""

import os
import uuid
from collections.abc import Iterable
from datetime import datetime
from typing import Any

import pytz
import streamlit as st
from lancedb.table import Table as KBaseTable

import src.constants as cst
from src.app_utils import connect_to_llm, init_st_keys, load_image
from src.app_widgets import create_button, create_chat_msg, create_first_assistant_msg, show_chat_history, show_md_file
from src.llm_api import build_full_llm_chat_input, stream_chat_response
from src.mongodb import MongodbClient, get_mongodb_config, save_chat_history
from src.prompt_building import WELCOME_MSG, extract_context_from_msg
from src.retrieval import connect_to_lancedb_table

# Chat Parameters
# -----------------------------
BOT_AVATAR = load_image(cst.BOT_AVATAR)
chat_config: dict[str, Any] = cst.get_rag_config()["chat"]
AVATARS: dict[str, Any] = {"assistant": BOT_AVATAR, "user": chat_config["user_avatar"]}
STREAM_DEFAULT: bool = chat_config["stream_default"]
CHAT_HISTORY_HEIGHT: int = chat_config["chat_history_height"]
SHOW_HAL_WARNING: int = 2  # after 1 user question show hallucination warning
HAL_WARNING_MSG: str = (
    "Please note that with the current state of technology, the digital assistant may hallucinate! 🙃"
)
ASK_USER_FEEDBACK: int = 2  # after 1 user questions ask user feedback


# LLM Parameters
# -----------------------------
llm_config: dict[str, Any] = cst.get_rag_config()["llm"]
LLM_TEMP: float = llm_config["settings"]["model_temp"]
LLM_API_NAME: str = llm_config["settings"]["api_name"]
LLM_API_CONFIG: dict[str, Any] = llm_config["api"][LLM_API_NAME]
LLM_API_KEY_NAME: str = LLM_API_CONFIG["key_name"]
LLM_API_KEY_URL: str = LLM_API_CONFIG["key_url"]
TOTAL_MAX_TOKEN: int = LLM_API_CONFIG["token"]["total_max"]


# Secrets
# -----------------------------
DEPLOYED: bool = st.secrets.get("deployed", False)
LLM_API_KEY: str = st.secrets.get(LLM_API_KEY_NAME, st.session_state.get(LLM_API_KEY_NAME, ""))


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
    create_chat_msg(user_prompt, role="user", avatar=avatars["user"])

    # create assistant response
    client = st.session_state["llm_client"]
    with st.spinner("I'm thinking..."):
        with st.chat_message("assistant", avatar=avatars["assistant"]):
            # build LLM chat input
            # TODO: check when message gets too big
            chat_history: list[dict[str, str]] = st.session_state["messages"]
            messages: list[dict[str, str]] = build_full_llm_chat_input(user_prompt, chat_history, k_base)
            # save first message, which contains context
            st.session_state["retrieval"].append(extract_context_from_msg(messages[0]["content"]))

            # send message to LLM and get response
            t_start = datetime.now()
            streamed_response_raw: Iterable = client.chat.completions.create(
                model=st.session_state["model_name"],
                messages=messages,
                temperature=st.session_state["model_temp"],
                stream=stream,
                # max_tokens=RESPONSE_MAX_TOKENS,
            )
            t_duration = datetime.now() - t_start
            token_current: int = st.session_state["total_tokens"]
            streamed_response_str: Iterable[str] = stream_chat_response(streamed_response_raw, api_name=api_name)
            token_delta: int = st.session_state["total_tokens"] - token_current
            full_response: str = st.write_stream(streamed_response_str)
    # Add assistant response to chat history
    st.session_state["messages"].append(
        {
            "role": "assistant",
            "content": full_response,
            "response_time": t_duration.total_seconds(),
            "token_delta": token_delta,
            "llm_usage": st.session_state["llm_usage"],
        }
    )


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
init_st_keys("deployed", DEPLOYED)
init_st_keys("llm_api_key_available", LLM_API_KEY != "")
init_st_keys(LLM_API_KEY_NAME, "")

# Page starts here
# ==========================
page_title = "Nutrition Insights with Dr. Greger's Digital Twin 🥦"
st.set_page_config(page_title=page_title, page_icon=BOT_AVATAR)  # , layout="wide")


# Header
# ------------
st.header(page_title, divider="blue")
app_intro: str = """
This digital assistant, inspired by [Dr. Michael Greger & his team](https://nutritionfacts.org/team/) at
[NutritionFacts.org](https://nutritionfacts.org/about/), is here to answer your questions about healthy eating and
lifestyle choices. Drawing from over 1,200 well-researched blog posts since 2011, it provides science-backed insights
to help you live a healthier, more informed life.
"""
if not st.session_state["start_chat"]:
    st.info(app_intro, icon="💡")

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
    mongodb_client = MongodbClient(**get_mongodb_config(DEPLOYED))
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

        # toggle option to enter own LLM API key
        # use_own_key = st.checkbox(label="Use own LLM API key", value=not st.session_state["llm_api_key_available"])

        if not st.session_state["llm_api_key_available"]:
            user_llm_key: str = st.text_input(
                label=(
                    f"Insert an [API KEY of '{LLM_API_NAME.capitalize()}']({LLM_API_KEY_URL}) here, since it's used as LLM API provider. It's for **free**! "
                    f'  \n_As a developer you could also add it to the `.streamlit/secrets.toml` file as `{LLM_API_KEY_NAME} = "..."`_.'
                ),
                placeholder=f"Enter your LLM API key of '{LLM_API_NAME.capitalize()}' here",
                type="password",
                key="user_llm_key",
                value="",
            )
            if user_llm_key:
                st.session_state["llm_api_key_available"] = True
                LLM_API_KEY = user_llm_key
                st.session_state[LLM_API_KEY_NAME] = user_llm_key

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

            if not LLM_API_KEY:
                st.error(f"The LLM API key for the API provider '{LLM_API_NAME}' is missing!", icon="❌")

# Chat-Control Container
# ------------
user_name = st.session_state["user_info"]["user_name"]
if st.session_state["submit_button"] and user_name and st.session_state["llm_api_key_available"]:
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
        chat_history = st.container(border=True, height=250 if new_chat else CHAT_HISTORY_HEIGHT)
        with chat_history:
            if reset_chat is True:
                st.success("Chat history has been reset.", icon="🗑️")

            # waking up assistant, if needed
            connect_to_llm(api_key=LLM_API_KEY, api_name=LLM_API_NAME, api_config=LLM_API_CONFIG)

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
            with chat_history:  # show everything below in the chat history
                t_start = datetime.now()
                process_user_input(user_prompt, avatars=AVATARS, api_name=LLM_API_NAME, k_base=k_base)
                t_duration = datetime.now() - t_start

            # save chat history
            if st.session_state["mongodb_connected"]:
                save_chat_history(
                    mongodb_client,
                    user_id=st.session_state["user_info"]["user_id"],
                    n_sessions=st.session_state["n_sessions"],
                    chat_history=st.session_state["messages"],
                    retrieval=st.session_state["retrieval"],
                )

        with chat_history:
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

        fb_options: list[str] = ["😞", "🙁", "😐", "🙂", "😀"]
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
            user_likes_bot: bool = user_fb in ["🙂", "😀"]

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
st.divider()
st.write(f"`LLM used: '{st.session_state['model_name'] or 'not yet defined'}'`")
st.write(
    f"`{st.session_state['total_tokens']/TOTAL_MAX_TOKEN:.0%}"
    " of conversation capacity used before a chat history reset is required.`"
)
with st.expander("🤓 _Debug Information_", expanded=False):
    st.button("Reset All 🧹", on_click=st.session_state.clear)
    st.write("Session State:")
    session_state: dict = dict(st.session_state)
    del session_state[LLM_API_KEY_NAME]
    st.json(session_state, expanded=False)

    # show env. variables
    st.write("Environment Variables:")
    st.json(dict(os.environ), expanded=False)
