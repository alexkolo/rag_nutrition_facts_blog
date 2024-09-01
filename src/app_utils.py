import time

import streamlit as st

from src.llm_api import get_llm_api_client_object, get_preferred_model


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


def connect_to_llm(api_key: str, api_name: str, api_config: dict):
    # Setup Model Name
    init_st_keys("model_name")
    if not st.session_state["model_name"]:
        model_name: str = api_config.get("model", {}).get("name", "")
        if not model_name:
            models_url: str = api_config.get("models", {}).get("url", "")
            ranked_models: list[str] = api_config.get("models", {}).get("ranked", [])
            model_name = get_preferred_model(api_key=api_key, models_url=models_url, ranked_models=ranked_models)
        st.session_state["model_name"] = model_name

    # Setup LLM API Client
    init_st_keys("llm_client")
    if not st.session_state["llm_client"]:
        with st.spinner("😴 Waking up for the digital clone..."):
            llm_api_client = get_llm_api_client_object(api_name=api_name)
            st.session_state["llm_client"] = llm_api_client(api_key=api_key)
        st.success("The digital clone is awake!", icon="✅")
