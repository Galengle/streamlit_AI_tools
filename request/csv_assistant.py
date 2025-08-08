import importlib.util
import os

import pandas as pd
import streamlit as st

from langchain.memory import ConversationBufferMemory

# 直接从文件路径导入utils.py
utils_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'utils.py')
spec = importlib.util.spec_from_file_location("utils", utils_path)
utils_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(utils_module)

# 获取LangChainHelper类
LangChainHelper = utils_module.LangChainHelper

st.header("💡 CSV数据分析智能工具")
with st.sidebar:
    openai_api_key = st.text_input("请输入OpenAI API密钥：", type="password")
    st.markdown("[获取OpenAI API密钥](https://platform.openai.com/account/api-keys)")

lch = LangChainHelper(api_key=openai_api_key, model="gpt-4-turbo", temperature=0)

# 定义图表可视化方式
def create_chart(input_data, chart_type):
    df_data = pd.DataFrame(input_data["data"], columns=input_data["columns"])
    df_data.set_index(input_data["columns"][0], inplace=True)
    if chart_type == "bar":
        st.bar_chart(df_data)
    elif chart_type == "line":
        st.line_chart(df_data)
    elif chart_type == "scatter":
        st.scatter_chart(df_data)


if "memory3" not in st.session_state:
    st.session_state["memory3"] = ConversationBufferMemory(
        return_messages=True,
        memory_key="chat_history",
        output_key="answer"
    )

uploaded_file = st.file_uploader("上传你的CSV文件：", type="csv")
df = None
if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    with st.expander("原始数据"):
        st.dataframe(df)

query = st.text_area("请输入你关于以上表格的问题，或数据提取请求，或可视化要求（支持散点图、折线图、条形图）：",
                     disabled=not uploaded_file)
button = st.button("生成回答")

if button and not openai_api_key:
    st.info("请输入你的OpenAI API密钥")
if button and not uploaded_file:
    st.info("请先上传数据文件")
if button and openai_api_key and uploaded_file:
    with st.spinner("AI正在思考中，请稍等..."):
        response_dict = lch.dataframe_agent(df, query)
        if "answer" in response_dict:
            st.write(response_dict["answer"])
        if "table" in response_dict:
            st.table(pd.DataFrame(response_dict["table"]["data"],
                                  columns=response_dict["table"]["columns"]))
        if "bar" in response_dict:
            create_chart(response_dict["bar"], "bar")
        if "line" in response_dict:
            create_chart(response_dict["line"], "line")
        if "scatter" in response_dict:
            create_chart(response_dict["scatter"], "scatter")
