import re
from langchain_experimental.utilities.python import PythonREPL


class PythonExecutor:
    def __init__(self, llm):
        self.llm = llm

    def invoke(self, query):
        code_message = self.llm.invoke(f"Generate python code based on user request:\n{query}")
        return self.execute(code_message)

    def execute(self, code_message):
        code = self._parse_python(message=code_message)
        return PythonREPL().run(code)

    def _parse_python(self, message):
        if hasattr(message, 'content'):
            message = message.content
        python_matching = re.search(r'```python(.+?)```', message, re.DOTALL | re.IGNORECASE)
        code_matching = re.search(r'```(.+?)```', message, re.DOTALL | re.IGNORECASE)

        if python_matching:
            return python_matching.group(1)
        elif code_matching:
            return code_matching.group(1)
        else:
            return message
