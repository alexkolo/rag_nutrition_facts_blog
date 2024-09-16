import os
from collections.abc import Iterable
from typing import Any

import requests
import streamlit as st
from dotenv import load_dotenv
from groq import Groq
from lancedb.table import Table

import src.constants as cst
from src.prompt_building import build_system_msg
from src.retrieval import get_context

LLM_CLIENTS: dict[str, Any] = {"groq": Groq}


def get_model_list(api_key: str, models_url: str) -> list[dict]:
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    try:
        response = requests.get(url=models_url, headers=headers, timeout=5)
        response.raise_for_status()  # Raise an HTTPError for bad responses
    # cache a 401 error, Unauthorized  and say that api key wrong
    except requests.exceptions.HTTPError as e:
        if response.status_code == 401:
            raise ValueError("You probably provided an invalid API key.")
        raise e

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


def get_llm_api_client_object(api_name: str) -> Any:
    LLMClient = LLM_CLIENTS.get(api_name)
    if not LLMClient:
        raise ValueError(f"Unsupported LLM provider: {api_name}")
    return LLMClient


def build_full_llm_chat_input(
    user_prompt: str,
    chat_history: list[dict[str, str]],
    k_base: Table,
    retriever_config: dict,
) -> list[dict[str, str]]:
    """
    Build the full chat history for the LLM where the system message contains the context for the most
    recent user message and is inserted at the beginning of the chat history.

    Parameters
    ----------
    user_prompt : str
        Most recent user prompt to send to the LLM, for which to retrieve context.
    chat_history : list[dict[str, str]]
        Full chat history from chatbot interaction with user.
    k_base : Table
        Knowledge base to retrieve context from.
    retriever_config: dict
        Configuration for the retriever

    Returns
    -------
    list[dict[str, str]]
        Full list of messages to send to the LLM.
    """
    # get the context for the most recent user prompt
    prompt_context: str = get_context(k_base, user_prompt, **retriever_config)
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
            usage = chunk.x_groq.usage
            st.session_state["total_tokens"] = usage.total_tokens
            st.session_state["llm_usage"] = {
                "prompt_tokens": usage.prompt_tokens,
                "completion_tokens": usage.completion_tokens,
                "total_tokens": usage.total_tokens,
                "prompt_time": usage.prompt_time,
                "completion_time": usage.completion_time,
                "total_time": usage.total_time,
            }
            """
            https://console.groq.com/docs/api-reference#chat-create
            "usage": {
                "prompt_tokens": 24,
                "completion_tokens": 377,
                "total_tokens": 401,
                "prompt_time": 0.009,
                "completion_time": 0.774,
                "total_time": 0.783
            }
            """
        else:
            yield text


def get_llm_model_name(api_config: dict[str, Any], api_key: str) -> str:
    model_name: str = api_config.get("model", {}).get("name", "")
    if not model_name:
        MODELS_URL: str = api_config.get("models", {}).get("url", "")
        RANKED_MODELS: list[str] = api_config.get("models", {}).get("ranked", [])
        model_name = get_preferred_model(api_key=api_key, models_url=MODELS_URL, ranked_models=RANKED_MODELS)

    return model_name


def setup_llm_client() -> tuple[Any, str, str]:
    # LLM Parameters
    LLM_CONFIG: dict[str, Any] = cst.get_rag_config()["llm"]
    LLM_API_NAME: str = LLM_CONFIG["settings"]["api_name"]
    LLM_API_CONFIG: dict[str, Any] = LLM_CONFIG["api"][LLM_API_NAME]

    # secrets
    load_dotenv(cst.REPO_PATH)
    LLM_API_KEY_NAME: str = LLM_API_CONFIG["key_name"].upper()
    LLM_API_KEY: str = os.getenv(LLM_API_KEY_NAME)

    # Model Name
    model_name: str = get_llm_model_name(api_config=LLM_API_CONFIG, api_key=LLM_API_KEY)

    # Patch the OpenAI client
    LLMClient = get_llm_api_client_object(api_name=LLM_API_NAME)
    llm_client = LLMClient(api_key=LLM_API_KEY)

    # return the LLM client and the model name
    return llm_client, LLM_API_NAME, model_name
