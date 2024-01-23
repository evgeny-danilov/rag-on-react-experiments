
from dotenv import load_dotenv, find_dotenv

from langchain_openai import ChatOpenAI
from langchain.cache import SQLiteCache
from langchain.globals import set_llm_cache

from utils.llm_calls_tracer import LlmCallsTracer

load_dotenv(find_dotenv())
set_llm_cache(SQLiteCache(database_path=".cache.db"))


class GPT_MODELS:
    gpt_4_128K_2023 = "gpt-4-1106-preview"  # $0.01/$0.03 per 1K tokens
    gpt_3_16K_2021 = "gpt-3.5-turbo-1106"  # $0.001/$0.002 per 1K tokens


class MyOpenAIWrapper:
    def __init__(self, temperature, model_name):
        self.temperature = temperature
        self.model_name = model_name

    def llm(self):
        llm_calls_tracer = LlmCallsTracer(file='output.log')

        return ChatOpenAI(
            temperature=self.temperature,
            model_name=self.model_name,
            callbacks=[llm_calls_tracer]
        )
