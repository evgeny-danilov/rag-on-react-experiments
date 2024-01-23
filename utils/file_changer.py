import os
import re
import pdb
import json
from typing import List

from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import ChatPromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field, validator

from .git_helpers import GitFilesLister


class File(BaseModel):
    file_path: str = Field(..., description="The relative path, including file name")
    content: str = Field(..., description="The content of the file")


class FileList(BaseModel):
    files: List[File] = Field(..., description="List of files to change")


class FileChanger:
    # UPSET_TEMPLATE = """
    # Given project structure:
    # {{ project_structure }}
    #
    # Request: {{ user_request }}
    #
    # Output template:
    # {{ output_template }}
    # """.strip()
    UPSET_TEMPLATE = """
    Format the message
    {{ user_request }}

    {{ output_template }}
    """.strip()

    def __init__(self, llm, directory):
        self.llm = llm
        self.directory = directory
        self.project_structure = GitFilesLister(directory=directory).list_files()
        self.parser = PydanticOutputParser(pydantic_object=FileList)

    def invoke(self, user_request):
        # required_change = self._input_code_cleaner(message=user_request)
        # self._upset_file(file_path=required_change['file_path'], content=required_change['content'])
        # return required_change

        prompt = self._upset_prompt()
        chain = prompt | self.llm | self.parser

        required_changes = chain.invoke({
            # 'project_structure': self.project_structure,
            'user_request': user_request,
            'output_template': self.parser.get_format_instructions()
        })

        for required_change in required_changes.files:
            self._upset_file(file_path=required_change.file_path, content=required_change.content)
        return 'File has been created/updated'

    def _upset_prompt(self):
        return ChatPromptTemplate.from_template(self.UPSET_TEMPLATE, template_format='jinja2')

    def _upset_file(self, file_path, content):
        full_path = os.path.join(self.directory, file_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, 'w') as file:
            file.write(content)

    def _input_code_cleaner(self, message):
        cleaned_str = re.sub(r'^```[a-z]*\n', '', message, flags=re.MULTILINE)
        cleaned_str = cleaned_str.rstrip('`')
        # cleaned_str = cleaned_str.replace('\n', '\\n')
        return json.loads(cleaned_str)


if __name__ == '__main__':
    from my_openai_wrapper import MyOpenAIWrapper, GPT_MODELS

    llm = MyOpenAIWrapper(temperature=0, model_name=GPT_MODELS.gpt_4_128K_2023).llm()

    project_dir = "../_test_projects/flight-service/api/"

    changes = FileChanger(llm=llm, directory=project_dir).invoke("Cover AggregateRoutesWorker by specs")

    print(changes)
