from langchain import hub
from langchain.agents import AgentExecutor, Tool, create_react_agent
from langchain_community.callbacks import get_openai_callback

from utils.my_openai_wrapper import MyOpenAIWrapper, GPT_MODELS
from utils.files_helpers import (FoldersStructure, FoldersStructureAnalyzer,
                                 CustomDirectoryLoader, CustomUnstructuredFileLoader)

project_dir = "../../enedis/client-artifacts/drive-download-20231023T125422Z-001"
# project_dir += "example/code/subversion.homeshore.be/svn/interclear/branches/"

llm = MyOpenAIWrapper(temperature=0, model_name=GPT_MODELS.gpt_4_128K_2023).llm()
# llm = MyOpenAIWrapper(temperature=0, model_name=GPT_MODELS.gpt_3_16K_2021).llm()
folder_structure = FoldersStructure(directory=project_dir)
project_analyzer = FoldersStructureAnalyzer(directory=project_dir, llm=llm)

custom_documents_loader = CustomDirectoryLoader(directory=project_dir)
custom_unstructured_file_loader = CustomUnstructuredFileLoader(directory=project_dir)

tools = [
    # Tool(
    #     name='Analyse files structure',
    #     func=project_analyzer.invoke,
    #     description="Summary project files structure. Receive text query as input parameter"),
    # Tool(
    #     name='Folders structure',
    #     func=folder_structure.list_only_dirs,
    #     description='Provide list of all folders and sub-folders'),
    Tool(
        name='Files structure',
        func=lambda x: FoldersStructure(directory=project_dir, include_files=True).parse(x),
        description="To get list of all files, Input parameter: '/' or any of existing sub-directory's, like 'docs/' or 'docs/res'"),
    Tool(
        name='Preview documents in folder',
        func=custom_documents_loader.invoke,
        description="To preview all files content in a given sub-folder. Input parameter: '/' or any of existing sub-directory's, like 'docs/' or 'docs/res'"),
    Tool(
        name='Read document in details',
        func=custom_unstructured_file_loader.invoke,
        description="To read the full content of a single file. Input parameter: exact file name, existing in file structure"),
]

prompt = hub.pull("hwchase17/react")
agent = create_react_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

# question = "What is the project about"
question = "Highlight major updated from the last business update"
question = "What is DAO in the scope of current project"

with get_openai_callback() as token_used:
    print(agent_executor.invoke({"input": question}))
    print(token_used)
