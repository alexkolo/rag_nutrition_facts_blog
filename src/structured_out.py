from collections.abc import Iterable
from enum import Enum
from typing import Any

import instructor
from pydantic import BaseModel, Field

import src.constants as cst
from src.app_utils import stream_text
from src.llm_api import setup_llm_client


# Define your desired output structure
class UserInfo(BaseModel):
    name: str
    age: int


class TicketCategory(str, Enum):
    """Enumeration of categories for incoming tickets."""

    GENERAL = "general"
    ORDER = "order"
    BILLING = "billing"
    OTHER = "other"


# Define your desired output structure using Pydantic
class Reply(BaseModel):
    content: str = Field(description="Your reply that we send to the customer.")
    category: TicketCategory = Field(description="Correctly assign one of the predefined categories")


if __name__ == "__main__":
    # LLM Parameters
    LLM_CONFIG: dict[str, Any] = cst.get_rag_config()["llm"]
    LLM_TEMP: float = LLM_CONFIG["settings"]["model_temp"]

    # Setup LLM API Client
    llm_client, llm_api_name, llm_model_name = setup_llm_client()
    print(llm_model_name)

    if llm_api_name == "groq":
        client = instructor.from_groq(client=llm_client)
    elif llm_api_name == "openai":
        client = instructor.from_openai(client=llm_client)
    elif llm_api_name == "anthropic":
        client = instructor.from_anthropic(client=llm_client)
    else:
        raise ValueError(f"Unsupported LLM provider: {llm_api_name}")

    chat_config = {
        "model": llm_model_name,
        "temperature": LLM_TEMP,
        "max_retries": 1,
    }

    # 1st simple example
    # -----------------------------
    messages = [{"role": "user", "content": "John Doe is 30 years old."}]
    user_info: UserInfo
    user_info, completion = client.chat.completions.create_with_completion(
        response_model=UserInfo, messages=messages, stream=False, **chat_config
    )

    print(user_info.name)
    print(user_info.age)

    # steaming
    user_stream01: Iterable[UserInfo] = client.chat.completions.create_partial(
        response_model=UserInfo, messages=messages, stream=True, **chat_config
    )

    for chunk in user_stream01:
        name = chunk.name
        if name != "":
            print(name, end="")
    print(".end streaming")
    print(chunk.name)
    print(chunk.age)

    # 2nd example
    # -----------------------------
    query = "Hi there, I have a question about my bill. Can you help me?"
    messages = [
        {
            "role": "system",
            "content": "You're a helpful customer care assistant that can classify incoming messages and create a response.",
        },
        {"role": "user", "content": query},
    ]

    reply: Reply
    reply, completion = client.chat.completions.create_with_completion(
        response_model=Reply,
        messages=messages,
        stream=False,
        **chat_config,
    )

    print(reply.content)
    print(reply.category)

    for chunk in stream_text(reply.content, sleep=1):
        print(chunk, end="")
    print("\nEnd streaming")

    print(completion.to_dict().get("usage"))

    # streamed
    user_stream02: Iterable[Reply] = client.chat.completions.create_partial(
        response_model=Reply,
        messages=messages,
        stream=True,
        **chat_config,
    )

    print("Streaming...")
    # for chunk in user_stream02:
    #     time.sleep(1)
    #     content = chunk.content
    #     # if content != "":
    #     print(content, end="")

    for extraction in user_stream02:
        # time.sleep(1)
        obj = extraction.model_dump()
        print(obj.get("content"))

    print("\n.End streaming")
    print(extraction.model_dump_json(indent=2))
    # print(chunk.content)
    # print(chunk.category)
