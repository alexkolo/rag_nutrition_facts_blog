from collections.abc import Iterable
from typing import Any

import streamlit as st

from src.app_utils import init_st_keys, stream_text


def show_md_file(path, **kwargs):
    with open(path, encoding="utf-8") as f:
        content = f.read()
    if kwargs:
        st.markdown(content.format(**kwargs))
    else:
        st.markdown(content)


def create_button(state_key: str, label: str, default: bool = False, **kwargs) -> bool:
    init_st_keys(state_key, default)

    def click_button():
        st.session_state[state_key] = True

    st.button(label=label, key=f"widget_{state_key}", on_click=click_button, **kwargs)

    return st.session_state[state_key]


def create_chat_msg(
    content: str | Iterable[str],
    role: str,
    avatar: Any = None,
    stream: bool = False,
    state_key: str = "messages",
):
    full_content: str
    with st.chat_message("assistant", avatar=avatar):
        if stream:
            full_content = st.write_stream(content)  # type: ignore
        else:
            st.write(content)
            full_content = str(content)
    # Add assistant response to chat history
    st.session_state[state_key].append({"role": role, "content": full_content})


def create_first_assistant_msg(msg: str, stream: bool = False, **kwargs):
    # show 1st assistant message in the chat history
    create_chat_msg(content=stream_text(msg) if stream else msg, role="assistant", stream=stream, **kwargs)


def show_chat_history(avatars: dict[str, Any], state_key: str = "messages"):
    # show chat message history
    for msg_dict in st.session_state[state_key]:
        role: str = msg_dict["role"]
        with st.chat_message(name=role, avatar=avatars[role]):
            st.write(msg_dict["content"])
