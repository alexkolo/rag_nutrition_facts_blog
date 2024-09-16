"""
Requires:
> docker-compose --file docker-langfuse.yml up --build
> pip install langfuse==2.48.1

Credentials (for local testing only):
loging: `test : testtest`
organization: "test-org"
project: "test-project"
secrete key:sk-lf-567e7ef6-8e62-41bc-8585-f5b54d16d1f2
public key: pk-lf-bb471e42-6666-4ab7-833c-3cf627834eaa
"""

import os
from typing import Any

from dotenv import load_dotenv
from groq import Groq
from langfuse.decorators import langfuse_context, observe

import src.constants as cst
from src.llm_api import get_llm_model_name


@observe(as_type="generation")
def groq_completion(client: Groq, **kwargs):
    # based on: https://langfuse.com/docs/sdk/python/decorators#log-any-llm-call

    # optional, extract some fields from kwargs
    kwargs_clone = kwargs.copy()
    input = kwargs_clone.pop("messages", None)
    model = kwargs_clone.pop("model", None)
    langfuse_context.update_current_observation(input=input, model=model, metadata=kwargs_clone)

    response = client.chat.completions.create(**kwargs)

    # See docs for more details on token counts and usd cost in Langfuse
    # https://langfuse.com/docs/model-usage-and-cost
    langfuse_context.update_current_observation(
        usage={
            "input": response.usage.prompt_tokens,
            "output": response.usage.completion_tokens,
        }
    )

    # return result
    return response.choices[0].message.content


@observe()
def ask_llm(messages: dict, api_key_name: str, **kwargs) -> str:
    llm_client = Groq(api_key=os.getenv(api_key_name))
    return groq_completion(client=llm_client, messages=messages, **kwargs)


if __name__ == "__main__":
    # LLM Parameters
    LLM_CONFIG: dict[str, Any] = cst.get_rag_config()["llm"]
    LLM_TEMP: float = LLM_CONFIG["settings"]["model_temp"]
    LLM_API_NAME: str = LLM_CONFIG["settings"]["api_name"]
    LLM_API_CONFIG: dict[str, Any] = LLM_CONFIG["api"][LLM_API_NAME]
    LLM_BASE_URL: str = LLM_API_CONFIG["base_url"]

    # secrets
    load_dotenv(cst.REPO_PATH)
    LLM_API_KEY_NAME = LLM_API_CONFIG["key_name"].upper()
    LLM_API_KEY: str = os.getenv(LLM_API_KEY_NAME)

    # Model Name
    model_name: str = get_llm_model_name(api_config=LLM_API_CONFIG, api_key=LLM_API_KEY)
    print(f"Model Name: {model_name}")
    chat_config = {"model": model_name, "temperature": LLM_TEMP}

    # Langfuse Credentials (for local testing only):
    os.environ["LANGFUSE_PUBLIC_KEY"] = "pk-lf-bb471e42-6666-4ab7-833c-3cf627834eaa"
    os.environ["LANGFUSE_SECRET_KEY"] = "sk-lf-567e7ef6-8e62-41bc-8585-f5b54d16d1f2"
    os.environ["LANGFUSE_HOST"] = "http://localhost:3000"

    # message
    # ---------
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Who was the first person to step on the moon?"},
        {
            "role": "assistant",
            "content": "Neil Armstrong was the first person to step on the moon on July 20, 1969, during the Apollo 11 mission.",
        },
        {"role": "user", "content": "What were his first words when he stepped on the moon?"},
    ]

    # test
    # ------------
    test = ask_llm(messages=messages, api_key_name=LLM_API_KEY_NAME, **chat_config)
    print(test)
