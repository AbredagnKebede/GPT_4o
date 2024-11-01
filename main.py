#GPT 3.5tobo open ai simulation
import os
import json
import streamlit as st
import openai

#configuring openai api key 
working_dir = os.path.dirname(os.path.abspath(__file__))
config_data = json.load(open(f"{working_dir}/config.json"))
OPENAI_API_KEY = config_data["OPENAI_API_KEY"]
openai.api_key = OPENAI_API_KEY
#configuring streamlit page setting 
st.set_page_config(page_title = "GPT 4 ASTU",page_icon = "💬", layout = "centered")

#initializing chat session
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

st.title("🤖 GPT 4 ASTU")

for message in st.session_state.chat_history:
    with st.chat_history(message['role']):
        st.markdown(message['content'])
user_prompt = st.chat_input("Ask GPT ASTU... ")
if user_prompt:
     st.session_state.chat_history.append({'role':'user', 'content':user_prompt})
     