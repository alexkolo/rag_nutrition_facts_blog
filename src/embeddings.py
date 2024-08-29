import requests


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
