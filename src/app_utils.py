import time
from collections.abc import Iterable
from pathlib import Path
from typing import Any

import streamlit as st
from PIL import Image

from src.llm_api import get_llm_api_client_object, get_preferred_model


def init_st_keys(key: str | list[str], default_value=None):
    if isinstance(key, list):
        for k in key:
            init_st_keys(k, default_value)
    elif isinstance(key, str):
        if key not in st.session_state:
            st.session_state[key] = default_value


def stream_text(response: str, sleep: float = 0.05) -> Iterable[str]:
    for word in response.split():
        yield word + " "
        time.sleep(sleep)


def get_llm_model_name(
    api_config: dict[str, Any],
    api_key: str,
    user_provided_key: bool = False,
) -> str:
    model_name: str = api_config.get("model", {}).get("name", "")
    if not model_name:
        models_url: str = api_config.get("models", {}).get("url", "")
        ranked_models: list[str] = api_config.get("models", {}).get("ranked", [])
        try:
            model_name = get_preferred_model(api_key=api_key, models_url=models_url, ranked_models=ranked_models)
        except Exception:
            err_msg: str = "There was an error connecting to the LLM API provider 😢."
            if user_provided_key:
                err_msg += "  \nYou may have provided an invalid API KEY."
            st.error(f"{err_msg}  \nClick **Reset All** to start over.", icon="❌")
            raise

    if not model_name:
        st.error("The LLM model name remains undefined 😢. Click **Reset All** to start over.", icon="❌")

    return model_name


def connect_to_llm(api_key: str, api_name: str, api_config: dict, user_provided_key: bool = False):
    # Setup Model Name
    init_st_keys("model_name")
    if not st.session_state["model_name"]:
        model_name: str = get_llm_model_name(
            api_config=api_config,
            api_key=api_key,
            user_provided_key=user_provided_key,
        )
        st.session_state["model_name"] = model_name

    # Setup LLM API Client
    init_st_keys("llm_client")
    if not st.session_state["llm_client"]:
        with st.spinner("😴 Waking up for the digital assistant..."):
            llm_api_client = get_llm_api_client_object(api_name=api_name)
            st.session_state["llm_client"] = llm_api_client(api_key=api_key)
        st.success("The digital assistant is awake!", icon="✅")


@st.cache_data(ttl="1d", show_spinner=False)
def load_image(image_file: str | Path) -> Image.Image:
    return Image.open(image_file)
