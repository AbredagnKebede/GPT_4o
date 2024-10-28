#GPT 4open ai simulation
import os
import json
import streamlit as st
import openai
#configuration 
working_dir = os.path.dirname(os.path.abspath(__file__))
config = json.load(open(f"{working_dir}/config.json"))
