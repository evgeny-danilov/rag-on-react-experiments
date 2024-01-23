import os
from datetime import date

from dotenv import load_dotenv, find_dotenv
from langchain_community.callbacks import get_openai_callback
from langchain.chains import GraphCypherQAChain
from langchain.agents import AgentExecutor, Tool, create_react_agent
from langchain_community.graphs import Neo4jGraph
from utils.my_openai_wrapper import MyOpenAIWrapper
from langchain_community.vectorstores import Neo4jVector
from langchain_openai import OpenAIEmbeddings

load_dotenv(find_dotenv())

# llm = MyOpenAIWrapper(temperature=1, model_name='gpt-3.5-turbo-1106').llm()
llm = MyOpenAIWrapper(temperature=0, model_name='gpt-4-1106-preview').llm()
graph = Neo4jGraph(url=os.environ['NEO_DATABASE_URL'], username=os.environ['NEO_USER'], password=os.environ['NEO_PASSWORD'])
graph_qa_chain = GraphCypherQAChain.from_llm(llm, graph=graph, verbose=True)

vector_db = Neo4jVector.from_existing_graph(
    embedding=OpenAIEmbeddings(),
    url=os.environ["NEO_DATABASE_URL"],
    username=os.environ["NEO_USER"],
    password=os.environ["NEO_PASSWORD"],
    index_name="vector",  # default index name
    node_label="All",
    text_node_properties=["title", "text"],  # TODO: add "summary"
    embedding_node_property="embedding",
)

tools = [
    Tool(
        name='Graph Vector Search',
        func=vector_db.similarity_search,
        description='Semantic search information'),
    # TODO: take in mind using keyword search on Graph DB
    # Option 1 (easier, probably): use search_type='hybrid' parameter in Neo4jVector
    # Option 2: https://towardsdatascience.com/integrating-neo4j-into-the-langchain-ecosystem-df0e988344d2
    Tool(
        name='Graph QA',
        func=graph_qa_chain.invoke,
        description='Retrieve information'),
]

from langchain import hub
prompt = hub.pull("hwchase17/react")
agent = create_react_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

question = "Days to implement and price for tarfif F120A"

with get_openai_callback() as token_used:
    print(agent_executor.invoke({"input": question}))
    print(token_used)
