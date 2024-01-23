import json
import pdb
from datetime import datetime

from langchain.callbacks.base import BaseCallbackHandler

PRINTED_INPUT_PARAMS = ['model_name', 'temperature', 'stop', 'function_call', 'functions']


class LlmCallsTracer(BaseCallbackHandler):
    def __init__(self, file):
        self.file = file
        self.llm_call_index = 0
        with open(self.file, "w") as file:
            file.write("")
        super().__init__()

    def on_llm_start(self, *args, **kwargs):
        prompts = args[1]
        invocation_params = kwargs['invocation_params']
        filtered_params = {k: invocation_params[k] for k in PRINTED_INPUT_PARAMS if k in invocation_params}

        with open(self.file, "a") as file:
            self._write_llm_call_header(file)

            file.write(f"\n=== INVOCATION PARAMS ===\n")
            file.write(f'{json.dumps(filtered_params, indent=4)}\n')

            file.write(f"\n=== INPUT MESSAGE ===\n")
            for prompt in prompts:
                for line in prompt.splitlines():
                    file.write(f"{line}\n")

    def on_llm_end(self, *args, **kwargs):
        response = args[0]
        generations = response.generations[0]
        with open(self.file, "a") as file:
            file.write(f"\n=== OUTPUT MESSAGE ===\n")
            for generation in generations:
                file.write(f"{generation.text}\n\n\n")

    def _write_llm_call_header(self, file):
        self.llm_call_index += 1
        current_datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        second_line = f"*** LLM Call #{self.llm_call_index}, {current_datetime} ***"
        stars = '*' * len(second_line)

        file.write(f"{stars}\n")
        file.write(f"{second_line}\n")
        file.write(f"{stars}\n")
