import json
import os
import sys

import pandas as pd
from langchain import hub
from langchain.agents import create_structured_chat_agent, AgentExecutor
from langchain.chains.conversation.base import ConversationChain
from langchain.chains.conversational_retrieval.base import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain.prompts import ChatPromptTemplate
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_core.output_parsers import PydanticOutputParser
from langchain.tools import BaseTool, Tool
from langchain_experimental.agents import create_pandas_dataframe_agent, create_csv_agent
from langchain_experimental.agents.agent_toolkits import create_python_agent
from langchain_experimental.tools import PythonREPLTool
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.utilities import WikipediaAPIWrapper
from langchain_text_splitters import RecursiveCharacterTextSplitter

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)
print(f"Project root: {project_root}, sys.path: {sys.path}")
from prompt_template.xiaohongshu_prompt import system_template_text, user_template_text
from prompt_template.data_analysis_assistant_prompt import PROMPT_TEMPLATE
from models.xiaohongshu_model import XiaoHongShuModel

class LangChainHelper:
    def __init__(
            self,
            api_key: str,
            model: str = "gpt-3.5-turbo",
            openai_api_base: str = "https://api.aigc369.com/v1",
            temperature: float = 0.5
    ):
        self.openai_api_key = api_key
        # self.openai_api_base = openai_api_base
        # self.temperature = temperature
        self.model = ChatOpenAI(model=model, openai_api_key=api_key, temperature=temperature, openai_api_base=openai_api_base)

    def generate_video_script(self, subject, video_length):
        title_template = ChatPromptTemplate.from_messages(
            [
                ("human", "请为'{subject}'这个主题的视频想一个吸引人的标题")
            ]
        )
        script_template = ChatPromptTemplate.from_messages(
            [
                ("human",
                 """你是一位短视频频道的博主。根据以下标题和相关信息，为短视频频道写一个视频脚本。
                 视频标题：{title}，视频时长：{duration}分钟，生成的脚本的长度尽量遵循视频时长的要求。
                 要求开头抓住限球，中间提供干货内容，结尾有惊喜，脚本格式也请按照【开头、中间，结尾】分隔。
                 整体内容的表达方式要尽量轻松有趣，吸引年轻人。
                 脚本内容可以结合以下维基百科搜索出的信息，但仅作为参考，只结合相关的即可，对不相关的进行忽略：
                 ```{wikipedia_search}```""")
            ]
        )

        # model = ChatOpenAI(model="gpt-3.5-turbo", openai_api_key=api_key, temperature=creativity, openai_api_base=openai_api_base)

        title_chain = title_template | self.model
        script_chain = script_template | self.model

        title = title_chain.invoke({"subject": subject}).content

        # 添加异常处理和重试机制
        search_result = "未能获取到相关维基百科信息"
        # try:
        #     search = WikipediaAPIWrapper(lang="zh", top_k_results=2, doc_content_chars_max=2000,request_timeout=10)
        #     search_result = search.run(subject)
        # except Exception as e:
        #     print(f"维基百科搜索失败: {e}")
        #     search_result = "未能获取到相关维基百科信息"

        script = script_chain.invoke({
            "title": title,
            "duration": video_length,
            "wikipedia_search": search_result
        }).content

        return search_result, title, script


    def generate_xiaohongshu(self, theme):
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_template_text),
            ("user", user_template_text)
        ])
        output_parser = PydanticOutputParser(pydantic_object=XiaoHongShuModel)
        chain = prompt | self.model | output_parser
        result: XiaoHongShuModel = chain.invoke({
            "parser_instructions": output_parser.get_format_instructions(),
            "theme": theme
        })
        return result

    def clone_memory_chat(self, prompt: str, cbm: ConversationBufferMemory):
        chain = ConversationChain(llm=self.model, memory=cbm)
        resp = chain.invoke({"input": prompt})
        # print("clone_memory_chat: ", resp)
        return resp["response"]

    def pdf_chat_handler(self, cbm, uploaded_file, question: str):
        temp_file_path = "temp.pdf"
        with open(temp_file_path, "wb") as f:
            f.write(uploaded_file.read())
        loader = PyPDFLoader(temp_file_path)
        docs = loader.load()

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,  # 每块文本的最大长度
            chunk_overlap=40,  # 分割片段之间重叠的长度
            separators=["\n", "。", "！", "？", "，", "、", ""]  # 用于分割的字符
        )
        texts = text_splitter.split_documents(docs)

        embeddings_model = OpenAIEmbeddings(model="text-embedding-3-large",
                                            openai_api_key=self.openai_api_key,
                                            openai_api_base="https://api.aigc369.com/v1")

        db = FAISS.from_documents(texts, embeddings_model)
        retriever = db.as_retriever()

        # memory = ConversationBufferMemory(return_messages=True, memory_key='chat_history', output_key='answer')

        qa = ConversationalRetrievalChain.from_llm(
            llm=self.model,
            retriever=retriever,
            memory=cbm,
            # chain_type="stuff"
            return_source_documents=True  # 返回对应向量存储里检索出来传给模型的片段
        )
        resp = qa.invoke({"chat_history": cbm, "question": question})

        return resp

    def dataframe_agent(self, df, question: str):
        agent = create_pandas_dataframe_agent(
            llm=self.model,
            df=df,
            agent_executor_kwargs={"handle_parsing_errors": True},
            verbose=True,
            allow_dangerous_code = True
        )
        prompt = PROMPT_TEMPLATE + question
        response = agent.invoke({"input": prompt})
        try:
            response_dict = json.loads(response["output"])
        except Exception as e:
            print(f"JSON解析失败: {e}")
            response_dict = {"error": "JSON解析失败"}
        return response_dict

    def chat_agent_with_tools(self, question: str, df: pd.DataFrame=None):
        try:
            python_agent_executor = create_python_agent(
                llm=self.model,
                tool=PythonREPLTool(),
                verbose=True,
                agent_executor_kwargs={"handle_parsing_errors": True}
            )
            csv_agent_executor = create_pandas_dataframe_agent(
                llm=self.model,
                df=df,
                agent_executor_kwargs={"handle_parsing_errors": True},
                verbose=True,
                allow_dangerous_code=True # 出于安全考虑，必须显式启用 allow_dangerous_code=True 参数。
            )
            tools = [
                Tool(
                    name="Python代码工具",
                    description="""当你需要借助Python解释器时，使用这个工具。
                    用自然语言把要求给这个工具，它会生成Python代码并返回代码执行的结果。""",
                    func=python_agent_executor.invoke
                ),
                Tool(
                    name="CSV分析工具",
                    description="""当你需要回答有关xxx.csv文件的问题时，使用这个工具。
                    它接受完整的问题作为输入，在使用Pandas库计算后，返回答案。""",
                    func=csv_agent_executor.invoke
                ),
                TextLengthTool()
            ]
            chat_history = ConversationBufferMemory(
                memory_key='chat_history',
                return_messages=True
            )
            prompt = hub.pull("hwchase17/structured-chat-agent")
            agent = create_structured_chat_agent(
                llm=self.model,
                tools=tools,
                prompt=prompt
            )
            agent_executor = AgentExecutor.from_agent_and_tools(
                agent=agent,
                tools=tools,
                memory=chat_history,
                verbose=True,
                handle_parsing_errors=True
            )
            print("Agent created successfully!")
            return agent_executor.invoke({"input": question})

        except Exception as e:
            print(f"Error creating agent: {e}")


class TextLengthTool(BaseTool):
    name: str = "文本字数计算工具"
    description: str = "当你被要求计算文本的字数时，使用此工具"

    def _run(self, text: str) -> int:
        return len(text)


if __name__ == '__main__':
    import os

    lch = LangChainHelper(api_key=os.getenv("OPENAI_API_KEY"))
    # print(lch.generate_video_script("sora模型", 1))
    # print(lch.generate_xiaohongshu("大模型"))

    memory = ConversationBufferMemory(return_messages=True)
    print(lch.clone_memory_chat("牛顿提出过哪些知名的定律？", memory))
    print(lch.clone_memory_chat("我上一个问题是什么？", memory))