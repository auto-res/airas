from typing import Literal
from airas.utils.api_client.openai_client import OpenAIClient, OPENAI_MODEL
from airas.utils.api_client.google_genai_client import GoogelGenAIClient, VERTEXAI_MODEL


LLM_MODEL = Literal[OPENAI_MODEL, VERTEXAI_MODEL]


class LLMFacadeClient:
    def __init__(self, llm_name: LLM_MODEL):
        self.llm_name = llm_name
        if llm_name in OPENAI_MODEL.__args__:
            self.client = OpenAIClient()
        elif llm_name in VERTEXAI_MODEL.__args__:
            self.client = GoogelGenAIClient()
        else:
            raise ValueError(f"Unsupported LLM model: {llm_name}")

    def generate(self, message: str):
        return self.client.generate(model_name=self.llm_name, message=message)

    def structured_outputs(self, message: str, data_model):
        return self.client.structured_outputs(
            model_name=self.llm_name, message=message, data_model=data_model
        )
