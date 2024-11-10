#--- gpt-4o-mini openai simulation ---
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
st.set_page_config(
    page_title = "GPT 4 ASTU",
    page_icon = "💬",
    layout = "centered")

#initializing chat session that is a list appends the chat history
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

st.title("🤖 GPT 4 ASTU")

for message in st.session_state.chat_history:
    with st.chat_history(message['role']):
        st.markdown(message['content'])

#input field for users    
user_prompt = st.chat_input("Ask GPT ASTU... ")
page_intro = "This is a simulation of chat gpt 4 using pretrained OPENAI mode provided by openai. Model simulation was built by Abredagn Kebede, thrid year software student as ASTU"

if user_prompt:
    #add user message and display it
    st.chat_message('user').markdown(user_prompt)
    st.session_state.chat_history.append({'role': 'user', 'content': user_prompt})
    
    response = openai.chat.completions.create(
        model = "gpt-4o-mini",
        messages = [
            {'role': 'system', 'content': "You are my helpful assistant"},
            *st.session_state.chat_history
        ]
    )
    
    #storing the model's response or answer 
    assistant_response = response.choices[0].message.content

    #appending the the respons to our model data
    st.session_state.chat_history.append({'role':'assistant','content':assistant_response})

    #displaying the assistant respons
    with st.chat_message('assistant'):
        st.markdown(assistant_response)
else:
    print(page_intro)