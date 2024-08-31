from typing import Any

import requests
from groq import Groq

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
