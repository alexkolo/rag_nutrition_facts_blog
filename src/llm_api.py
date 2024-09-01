from collections.abc import Iterable
from typing import Any

import requests
import streamlit as st
from groq import Groq
from lancedb.table import Table

from src.prompt_building import build_system_msg
from src.retrieval import get_context

LLM_CLIENTS: dict[str, Any] = {"groq": Groq}


def get_model_list(api_key: str, models_url: str) -> list[dict]:
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    response = requests.get(url=models_url, headers=headers, timeout=5)
    response.raise_for_status()  # Raise an HTTPError for bad responses
    return response.json()["data"]


def get_preferred_model(api_key: str, models_url: str, ranked_models: list[str]) -> str:
    # get list of models
    model_list: list[dict] = get_model_list(api_key=api_key, models_url=models_url)
    # get active models
    active_model_ids: list[str] = [md["id"] for md in model_list if md["active"]]
    # pick preferred model
    for model in ranked_models:
        if model in active_model_ids:
            return model
    # if no model was found, raise an error
    raise ValueError("No preferred model found in the list of active models.")


def get_llm_api_client_object(api_name: str):
    return LLM_CLIENTS.get(api_name)


def build_full_llm_chat_input(
    user_prompt: str, chat_history: list[dict[str, str]], k_base: Table
) -> list[dict[str, str]]:
    """
    Build the full chat history for the LLM where the system message contains the context for the most
    recent user message and is inserted at the beginning of the chat history.

    Parameters
    ----------
    user_prompt : str
        Most recent user prompt to send to the LLM, for which to retrieve context.

    Returns
    -------
    list[dict[str, str]]
        Full list of messages to send to the LLM.
    """

    # get the context for the most recent user prompt
    # prompt_context: str = "Error: could not retrieve any context"  # TODO retrieve_context(user_prompt)
    prompt_context: str = get_context(k_base, user_prompt)
    # build the system message with the context
    system_msg_with_context: str = build_system_msg(context=prompt_context)
    # insert user prompt at the beginning of the chat history
    messages: list[dict[str, str]] = [{"role": "system", "content": system_msg_with_context}]
    # add the rest of the chat history to the LLM input
    messages.extend([{"role": msg["role"], "content": msg["content"]} for msg in chat_history])

    return messages


def stream_chat_response(response: Iterable, api_name: str) -> Iterable[str]:
    for chunk in response:
        text = chunk.choices[0].delta.content
        if text is None and api_name == "groq":
            st.session_state["total_tokens"] = chunk.x_groq.usage.total_tokens
        else:
            yield text
