"""
Start app: `streamlit run app.py`
View in browser: `http://localhost:8501`

TODO:
- connect knowledge base to app
- create user ID
- save user feedback & chat history into database
"""

from collections.abc import Iterable
from typing import Any

import streamlit as st
from lancedb.table import Table
from PIL import Image

import src.constants as cst
from src.app_utils import connect_to_llm, init_st_keys
from src.app_widgets import create_button, create_chat_msg, create_first_assistant_msg, show_chat_history, show_md_file
from src.llm_api import build_full_llm_chat_input, stream_chat_response
from src.prompt_building import WELCOME_MSG
from src.retrieval import get_knowledge_base

# Chat Parameters
# -----------------------------
BOT_AVATAR = Image.open(cst.BOT_AVATAR)
chat_config = cst.get_rag_config()["chat"]
avatars = {"assistant": BOT_AVATAR, "user": chat_config["user_avatar"]}
STREAM_DEFAULT: bool = chat_config["stream_default"]
CHAT_HISTORY_HEIGHT: int = chat_config["chat_history_height"]
show_hal_warning: int = 2  # after 1 user question show hallucination warning
hal_warning_msg: str = "Please note that with the current state of technology, the digital clone may hallucinate! 🙃"
ask_user_feedback: int = 4  # after 2 user questions ask user feedback

# LLM Parameters
# -----------------------------
llm_config = cst.get_rag_config()["llm"]
LLM_TEMP: float = llm_config["settings"]["model_temp"]
init_st_keys("model_temp", LLM_TEMP)
LLM_API_NAME: str = llm_config["settings"]["api_name"]
llm_api_config: dict = llm_config["api"][LLM_API_NAME]
LLM_API_KEY_NAME: str = llm_api_config["key_name"]
TOTAL_MAX_TOKEN: int = llm_api_config["token"]["total_max"]


# Secrets
# -----------------------------
LLM_API_KEY: str = st.secrets[LLM_API_KEY_NAME]

# Chat Bot Elements
# -----------------------------


def process_user_input(
    user_prompt: str,
    avatars: dict[str, Any],
    api_name: str,
    k_base: Table,
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

            # send message to LLM and get response
            streamed_response_raw: Iterable = client.chat.completions.create(
                model=st.session_state["model_name"],
                messages=messages,
                temperature=st.session_state["model_temp"],
                stream=stream,
                # max_tokens=RESPONSE_MAX_TOKENS,
            )
            streamed_response_str: Iterable[str] = stream_chat_response(streamed_response_raw, api_name=api_name)
            full_response: str = st.write_stream(streamed_response_str)
    # Add assistant response to chat history
    st.session_state["messages"].append({"role": "assistant", "content": full_response})


# Initialize chat history
# -----------------------------
init_st_keys("messages", [])
init_st_keys("submit_button", False)
init_st_keys("start_chat", False)
init_st_keys("total_tokens", 0)
init_st_keys("n_sessions", 1)
init_st_keys("user_info", cst.USER_INFO_TEMPLATE)
init_st_keys("model_temp", LLM_TEMP)

# Page starts here
# ==========================
page_title = "Chat with Dr. Greger's digital clone 🤖"
st.set_page_config(page_title=page_title, page_icon=BOT_AVATAR)  # , layout="wide")

# Header
# ------------
st.header(page_title, divider="blue")

# Get Knowledge Base
# ------------
init_st_keys("kbase_loaded", False)
k_base: Table = get_knowledge_base()
st.session_state["kbase_loaded"] = True


# Top Container
# ------------
with st.container(border=False):
    with st.popover(
        "⚖ :red[**Please read this disclaimer before engaging with my digital clone:**]",
        use_container_width=True,
    ):
        # inspired by: https://cloud.docs.tamr.com/page/ai-chatbot-disclaimer
        # https://wow.groq.com/privacy-policy/
        show_md_file(cst.BOT_DISCLAIMER)

    left_button, middle_button, right_button = st.columns(3)
    with left_button:
        start_chat = create_button(
            "start_chat",
            "Wake up the digital clone ⏰",
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


# Chat box
if st.session_state["start_chat"]:
    new_chat: bool = not st.session_state["messages"]
    with st.container(border=False):
        # chat history
        chat_history = st.container(border=True, height=250 if new_chat else CHAT_HISTORY_HEIGHT)
        with chat_history:
            if reset_chat is True:
                st.success("Chat history has been reset.", icon="🗑️")

            # waking up assistant, if needed
            connect_to_llm(api_key=LLM_API_KEY, api_name=LLM_API_NAME, api_config=llm_api_config)

            if new_chat:
                # show 1st assistant message in the chat history
                create_first_assistant_msg(msg=WELCOME_MSG, avatar=BOT_AVATAR, stream=STREAM_DEFAULT)
            else:
                # show chat message history
                show_chat_history(avatars=avatars)

        # User input widget (at the bottom, outside of the chat history)
        user_prompt = st.chat_input(
            placeholder="Enter your question here, e.g 'How to eat healthy?'",
            key="user_input",
            max_chars=500,
            disabled=not st.session_state["start_chat"] or st.session_state["total_tokens"] >= TOTAL_MAX_TOKEN,
        )

        if user_prompt:
            with chat_history:  # show everything below in the chat history
                process_user_input(user_prompt, avatars=avatars, api_name=LLM_API_NAME, k_base=k_base)

            # # save chat history
            # if st.session_state["mongodb_connected"]:
            #     save_chat_history(
            #         mongodb_client,
            #         user_id=st.session_state["user_info"]["user_id"],
            #         n_sessions=st.session_state["n_sessions"],
            #         chat_history=st.session_state[MESSAGES],
            #     )

        with chat_history:
            if st.session_state["total_tokens"] >= TOTAL_MAX_TOKEN:
                st.error("Chat history is too long. Please reset it.", icon="🚫")

    # show warning
    # ----------------------
    if len(st.session_state["messages"]) > show_hal_warning:
        st.warning(hal_warning_msg)

    # Ask for user feedback
    # ----------------------
    if len(st.session_state["messages"]) > ask_user_feedback:
        init_st_keys("user_rating")
        fb_disabled: bool = st.session_state["user_rating"] is not None

        # st.write("Do you find my digital clone helpful?")
        fb_options: list[str] = ["😞", "🙁", "😐", "🙂", "😀"]
        with st.form(key="feedback_form", border=True):
            user_fb = st.radio(
                label="**Please let me know how helpful you find my digital clone:**",
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
            # with st.spinner("Saving your feedback..."):
            #     user_id: str = st.session_state["user_info"]["user_id"]
            #     if st.session_state["mongodb_connected"]:
            #         mongodb_client.update_single_field(
            #             filter={"user_id": user_id},
            #             field="like_bot",
            #             value=value,
            #         )
            st.success("Thank you for your feedback!", icon="💚" if user_likes_bot else "🙏")

# Debug
# ==============
st.divider()
st.write(f"`{st.session_state['total_tokens']/TOTAL_MAX_TOKEN:.0%} of conversation capacity used.`")
with st.expander("🤓 _Debug Information_", expanded=False):
    st.button("Reset All 🧹", on_click=st.session_state.clear)
    st.write(st.session_state)
