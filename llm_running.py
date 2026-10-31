##creator Junlin Lyu
##llm运行

import os
from dotenv import load_dotenv
from openai import OpenAI

import examples

load_dotenv()
##配置导入
client = OpenAI(api_key=os.getenv("LLM_API_KEY"),
                base_url = os.getenv("LLM_BASE_URL"))

model = os.environ.get("LLM_MODEL", "deepseek-chat")


##创建prompt
system = """ 你是一名资深的数据分析师，你可以把用户的中文问题翻译成DuckDB 的 SQL
数据库的结构和字段是：
{schema}
{metrics}
{examples}
规则：
1. 只能输出一条SQL，不要解释，不要markdown 代码块
2. 只允许select
3. 数据的时间范围规定在 2016-09-04 到 2018-10-17
4. 一个订单可能有多条 order_items 记录，聚合时注意订单层级
5. price 是商品金额，freight_value 是运费


问题{q}

SQL：
"""

def build_prompt(schema, q, metrics = "", examples = ""):
    return system.format(schema = schema, q = q, metrics = metrics, examples =examples)

##调用执行
def ask(schema, q, metrics = "", examples = ""):
    response = client.chat.completions.create(

        model = model,
        messages = [{"role":"user", "content": build_prompt(schema, q, metrics, examples)}],
        temperature = 0
    )
    return response.choices[0].message.content.strip(), response.usage

def clean_sql(text):
    text = text.replace("```sql", "").replace("```", "")
    return text.strip()


