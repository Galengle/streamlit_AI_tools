from typing import List

from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

class XiaoHongShuModel(BaseModel):
    titles: List[str] = Field(description="小红书的5个标题", min_items=5, max_items=5, example=["三体", "盗墓笔记", "1984"])
    content: str = Field(description="小红书的文章内容", example="小红书的文章内容")


