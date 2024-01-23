import pdb
from datetime import date

from langchain import hub
from langchain.agents import AgentExecutor, Tool, create_react_agent

from langchain_community.utilities import SerpAPIWrapper
from langchain_community.callbacks import get_openai_callback
from langchain_community.docstore.wikipedia import Wikipedia
from langchain_community.document_loaders import WikipediaLoader

from utils.my_openai_wrapper import MyOpenAIWrapper
from utils.python_executor import PythonExecutor


llm = MyOpenAIWrapper(temperature=0, model_name='gpt-4-1106-preview').llm()
# llm = MyOpenAIWrapper(temperature=0, model_name='gpt-3.5-turbo-1106').llm()

google_search = SerpAPIWrapper()
wiki_search = Wikipedia()
python_executor = PythonExecutor(llm=llm)


tools = [
    # Tool(
    #     name='Search in Google',
    #     func=google_search.run,
    #     description='To search an information in Google'),
    Tool(
        name='Search in Wiki',
        func=wiki_search.search,
        description='To search relevant pages in Wikipedia'),
    Tool(
        name='Parse Wiki page',
        func=lambda x: WikipediaLoader(query=x, load_max_docs=1).load(),
        description='To parse Wikipedia page. Input: page name'),
    Tool(
        name='Python executor',
        func=python_executor.execute,
        description="To build any kind of analytic, including collecting information from web pages. "
                    "Input: valid python code"),
    # Tool(
    #     name="Datetime",
    #     func=lambda x: date.today().isoformat(),
    #     description="Returns the current datetime"),
]

prompt = hub.pull("hwchase17/react")
agent = create_react_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

# question = "what is 123^23"
# question = "How old is the president of the United States"
# question = "What is political program of winned party in latest NL elections?"
question = ("What is the correlation between life expectancy and ACTUAL form of government in countries around the world. "
            "I'm interesting in de-facto form of governance. Make plan and solve it")

with get_openai_callback() as token_used:
    agent_executor.invoke({"input": question})
    print(token_used)
