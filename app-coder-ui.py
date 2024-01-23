import streamlit as st
import time
import json
from threading import Thread

from react_on_coding import react_on_coding


def parse_log_file(filepath):
    try:
        with open(filepath, 'r') as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def process_user_request():
    user_request = st.session_state.user_request
    st.session_state.final_action_found = False
    st.session_state.user_request = user_request
    st.session_state.steps = []
    thread = Thread(target=react_on_coding, args=(user_request,))
    thread.start()


def main():
    st.title('Code Copilot')

    if 'final_action_found' not in st.session_state:
        st.session_state.final_action_found = False

    st.text_input("User request", key="user_request")
    st.button("Submit", on_click=process_user_request)

    placeholder = st.empty()
    steps = parse_log_file('output-react-steps.log')
    with placeholder.container():
        for i, step in enumerate(steps):
            action = step.get('Action', 'N/A')
            if not action.startswith('Final Thought'):
                with st.expander(f"Step {i + 1}: {action}"):
                    st.markdown(f"**Thought:** {step.get('Thought', 'N/A')}")
                    if not action.startswith('Final Thought'):
                        st.markdown(f"**Action Input:** {step.get('Action Input', 'N/A')}")
                        st.markdown(f"**Action:** {action}")
                        st.markdown(f"**Observation:** {step.get('Observation', 'N/A')}")
            else:
                st.session_state.final_action_found = True
                st.markdown(f"##### Result")
                st.markdown(f"{step.get('Thought', 'N/A')}")
                st.markdown(f"**Summary:** {step.get('Final Answer', 'N/A')}")

    if len(steps) > 0 and not st.session_state.final_action_found:
        with st.spinner('Processing...'):
            time.sleep(5)
        time.sleep(0.5)
        st.rerun()


if __name__ == "__main__":
    main()