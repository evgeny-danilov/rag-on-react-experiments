import streamlit as st

from langchain_community.callbacks import StreamlitCallbackHandler
from langchain_community.chat_message_histories import StreamlitChatMessageHistory
from langchain_core.runnables import RunnableConfig

from react_on_coding import agent_executor

agent_executor.return_intermediate_steps = True
agent_executor.handle_parsing_errors = True
# agent_executor.memory = st.session_state.msg # TODO: check what it is

st.set_page_config(page_title="ReAct: Code copilot", page_icon="")
st.title("🦜 ReAct: Code copilot")

msgs = StreamlitChatMessageHistory()
if len(msgs.messages) == 0 or st.sidebar.button("Reset chat history"):
    # msgs.clear()
    msgs.add_ai_message("I'm your code assistant")
    st.session_state.steps = {}

avatars = {"human": "user", "ai": "assistant"}
for idx, msg in enumerate(msgs.messages):
    with st.chat_message(avatars[msg.type]):
        # Render intermediate steps if any were saved
        for step in st.session_state.steps.get(str(idx), []):
            if step[0].tool == "_Exception":
                continue
            with st.status(f"**{step[0].tool}**: {step[0].tool_input}", state="complete"):
                st.write(step[0].log)
                st.write(step[1])
        st.write(msg.content)

if prompt := st.chat_input(placeholder="Put your question or request to change the code"):
    msgs.clear()
    st.chat_message("user").write(prompt)

    with st.chat_message("assistant"):
        st.session_state.steps = {}

        st_cb = StreamlitCallbackHandler(st.container(), expand_new_thoughts=False)
        cfg = RunnableConfig()
        cfg["callbacks"] = [st_cb]

        response = agent_executor.invoke({'input': prompt}, cfg)
        st.write(response["output"])
        st.session_state.steps[str(len(msgs.messages) - 1)] = response["intermediate_steps"]


# TODO: Work with big coding files
#  Generate diff and inject to file

# TODO: Stability: Write tests and auto-fix the code
#   Use pytest

# TODO: Implement human in the loop
#  https://github.com/langchain-ai/langchain/issues/11626
#  https://stackoverflow.com/questions/77268592/how-to-integrate-langchains-human-tool-into-streamlit
#  https://python.langchain.com/docs/modules/agents/how_to/agent_iter

# TODO: For better history cleaning check an example:
#  https://github.com/langchain-ai/streamlit-agent/blob/main/streamlit_agent/mrkl_demo.py#L85
