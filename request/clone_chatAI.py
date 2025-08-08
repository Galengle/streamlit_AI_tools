import importlib.util
import os
import time

import streamlit as st

from langchain.memory import ConversationBufferMemory

# 直接从文件路径导入utils.py
utils_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'utils.py')
spec = importlib.util.spec_from_file_location("utils", utils_path)
utils_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(utils_module)

st.title("💬 克隆ChatGPT")

with st.sidebar:
    openai_api_key = st.text_input("请输入OpenAI API Key：", type="password")
    st.markdown("[获取OpenAI API key](https://platform.openai.com/account/api-keys)")

# 获取LangChainHelper类
LangChainHelper = utils_module.LangChainHelper
lch = LangChainHelper(api_key=openai_api_key)

if "memory1" not in st.session_state:
    st.session_state["memory1"] = ConversationBufferMemory(return_messages=True)
    st.session_state["messages"] = [{"role": "ai", "content": "你好，我是你的AI助手，有什么可以帮你的吗？"}]

for message in st.session_state["messages"]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

prompt = st.chat_input("Say something")
if prompt:
    if not openai_api_key:
        st.info("请输入你的OpenAI API Key")
        st.stop()
    st.session_state["messages"].append({"role": "user", "content": prompt})
    with st.chat_message("human"):
        st.markdown(prompt)
    with st.spinner("AI正在思考中，请稍等..."):
        response = lch.clone_memory_chat(prompt, st.session_state["memory1"])

    st.session_state["messages"].append({"role": "ai", "content": response})
    st.chat_message("ai").write(response)





