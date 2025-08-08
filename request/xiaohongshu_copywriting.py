import importlib.util
import os
import time

import streamlit as st

# 直接从文件路径导入utils.py
utils_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'utils.py')
spec = importlib.util.spec_from_file_location("utils", utils_path)
utils_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(utils_module)

# 获取LangChainHelper类
LangChainHelper = utils_module.LangChainHelper

st.header("爆款小红书AI写作助手 ✏️")
with st.sidebar:
    openai_api_key = st.text_input("请输入OpenAI API密钥：", type="password")
    st.markdown("[获取OpenAI API密钥](https://platform.openai.com/account/api-keys)")

lch = LangChainHelper(api_key=openai_api_key)

theme = st.text_input("💡 请输入小红书文案的主题：")
submit = st.button("开始写作")

if submit and not openai_api_key:
    st.info("请输入你的OpenAI API密钥")
    st.stop()
if submit and not theme:
    st.info("请输入生成内容的主题")
    st.stop()
if submit:
    time_start = time.time()
    with st.spinner("AI正在努力创作中，请稍等..."):
        result = lch.generate_xiaohongshu(theme)
    st.success(f"AI写作完成，用时{time.time() - time_start:.2f}秒")
    st.divider()
    left_column, right_column = st.columns(2)
    with left_column:
        st.markdown("##### 小红书标题1")
        st.write(result.titles[0])
        st.markdown("##### 小红书标题2")
        st.write(result.titles[1])
        st.markdown("##### 小红书标题3")
        st.write(result.titles[2])
        st.markdown("##### 小红书标题4")
        st.write(result.titles[3])
        st.markdown("##### 小红书标题5")
        st.write(result.titles[4])
    with right_column:
        st.markdown("##### 小红书正文")
        st.write(result.content)
