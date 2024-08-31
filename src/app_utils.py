import time
import streamlit as st


def init_st_keys(key: str | list[str], default_value=None):
    if isinstance(key, list):
        for k in key:
            init_st_keys(k, default_value)
    elif isinstance(key, str):
        if key not in st.session_state:
            st.session_state[key] = default_value


def stream_text(response: str):
    for word in response.split():
        yield word + " "
        time.sleep(0.05)
