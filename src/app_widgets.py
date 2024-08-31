from collections.abc import Iterable

import streamlit as st

from app_utils import init_st_keys


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
    avatar=None,
    stream: bool = False,
):
    full_content: str
    with st.chat_message("assistant", avatar=avatar):
        if stream:
            full_content = st.write_stream(content)  # type: ignore
        else:
            st.write(content)
            full_content = str(content)
    # Add assistant response to chat history
    st.session_state["messages"].append({"role": role, "content": full_content})
