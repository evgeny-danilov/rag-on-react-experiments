import pdb
import os
import re
import json

from langchain import hub
from langchain.agents import AgentExecutor, Tool, create_react_agent
from langchain_community.callbacks import get_openai_callback

from utils.my_openai_wrapper import MyOpenAIWrapper, GPT_MODELS
from utils.files_helpers import CustomUnstructuredFileLoader, FoldersStructure
from utils.file_changer import FileChanger
from utils.git_helpers import GitFilesLister
from utils.ruby_tests_runner import RubyTestsRunner
from utils.command_runner import CommandRunner

llm = MyOpenAIWrapper(temperature=0, model_name=GPT_MODELS.gpt_4_128K_2023).llm()

# Flight Service (Ruby)
# project_dir = "_test_projects/flight-service/api/"
# question = "Write tests for AggregateRoutesWorker. Take into account engineering guides"

# JDE (Python, Flask)
# project_dir = "_test_projects/coffee/"
# user_request = "Validate Users model"
# user_request = "Add DB table `new_product_generations` and run migration"
# user_request = "Add field 'text' to `new_product_generations` table and run migration"

# Content generator (demo-platform)
project_dir = "../../demo-plaform/aione/apps/content_generator"
user_request = "Say about the project"

file_changer = FileChanger(llm=llm, directory=project_dir)
custom_unstructured_file_loader = CustomUnstructuredFileLoader(directory=project_dir)
ruby_tests_runner = RubyTestsRunner(directory=project_dir)
command_runner = CommandRunner(directory=project_dir, llm=llm)
folder_structure = FoldersStructure(directory=project_dir, include_files=True)

# class CustTool(Tool):
#     def _run(self, *args, **kwargs):
#         pdb.set_trace()
#         super().run(args, kwargs)

tools = [
    Tool(
        name='Project structure',
        func=lambda x: GitFilesLister(directory=project_dir).list_files(x, max_depth=2),
        description="To get list of all files, Input parameter: '/' or any of existing sub-directory's, "
                    "like 'docs/' or 'docs/res'"),
    Tool(
        name='Read file',
        func=custom_unstructured_file_loader.invoke,
        description="To read content of a single file. Input value: exact file name in a project"),
    Tool(
        name='Upset file',
        func=file_changer.invoke,
        description='To create or modify file in project. Action input template: ```{"file_path": '
                    '"<The relative path, including file name>", "content": "<New content of file>"}```'),
    Tool(
        name='Run bush command',
        func=command_runner.invoke,
        description='Able to execute a command directly under the project directory. List of command is in README.md. '
                    'Input value: valid bash command, using single quotes'),
    # Tool(
    #     name='Ask User',
    #     func=None,
    #     description='To ask clarifications from user'),
]

prev_history = """
Thought: First of all read README.md to find relevant instructions
Action: Read file
Action Input: README.md
Observation: To add a new DB table:\n```bash\n\nstep 1: create file in app/models\n\nstep 2: include from app.models.model_name import ModelName into app/__init__.py\n\nstep 3: create migration file\n\nflask db migrate -m "msg"\n\nstep 4: update DB structure\n\nflask db upgrade\n```\n\n
"""

prev_history = ""


# def agent_executor():
prompt = hub.pull("hwchase17/react")
# prompt.template = prompt.template.replace("Thought:{agent_scratchpad}", "{prev_history}\nThought:{agent_scratchpad}")

agent = create_react_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)


def react_on_coding(user_request):
    # with get_openai_callback() as token_used:
    #     print(agent_executor.invoke({"input": user_request}))
    #     print(token_used)

    with get_openai_callback() as token_used:
        react_steps = 'output-react-steps.log'
        with open(react_steps, "w") as file:
            file.write("[]")

        for step in agent_executor.iter({"input": user_request, "prev_history": prev_history}):
            if intermediate_steps := step.get("intermediate_step"):
                step_info = intermediate_steps[0]
                if step_info[0].tool == 'Ask User':
                    break
                observation = step_info[1]
                log = step_info[0].log
                log_parts = re.findall(r'Thought: (.*?)\n\nAction: (.*?)\nAction Input: (.*)', log, re.DOTALL)
                if not log_parts:
                    log_parts = re.findall(r'(.*?)\n\nAction: (.*?)\nAction Input: (.*)', log, re.DOTALL)

                if log_parts:
                    step_dict = {
                        'Thought': log_parts[0][0],
                        'Action': log_parts[0][1],
                        'Action Input': log_parts[0][2],
                        'Observation': str(observation)
                    }
                else:
                    step_dict = {'Unknown format': str(step_info)}
            else:
                final_step = step['messages'][0].content
                thought, final_answer = final_step.split('Final Answer:')
                step_dict = {
                    'Thought': thought,
                    'Action': 'Final Thought',
                    'Final Answer': final_answer
                }

            with open(react_steps, 'r') as file:
                existing_steps = json.load(file)
            existing_steps.append(step_dict)

            with open(react_steps, 'w') as file:
                file.write(json.dumps(existing_steps, indent=2))


if __name__ == "__main__":
    react_on_coding(user_request=user_request)
