from typing import Protocol, cast

import numpy as np
import requests
from sentence_transformers import SentenceTransformer


class HuggingFaceEmbedder:
    # inspired by LangChain
    def __init__(self, model_name: str, api_key: str):
        self.model_name = model_name
        self.api_key = api_key

    def embed(self, texts: list[str]) -> list[list[float]]:
        api_url = (
            f"https://api-inference.huggingface.co/pipeline/feature-extraction/sentence-transformers/{self.model_name}"
        )
        response = requests.post(
            url=api_url,
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={
                "inputs": texts,
                "options": {"wait_for_model": True, "use_cache": True},
            },
        )
        return response.json()


class EmbeddingFunction(Protocol):
    """
    A protocol that represents a function for generating embeddings.

    Parameters
    ----------
    text : List[str]
        A list of strings for which embeddings are to be generated.

    Returns
    -------
    List[List[float]]
        A list of embeddings, where each embedding is represented as
        a list of floats.
    """

    def __call__(self, text: list[str]) -> list[list[float]]: ...


def create_local_emb_func(name: str, device: str = "cpu") -> EmbeddingFunction:
    emb_model = SentenceTransformer(name, device=device)

    def emb_func(text: list[str]) -> list[list[float]]:
        return cast(np.ndarray, emb_model.encode(sentences=text)).tolist()

    return emb_func
