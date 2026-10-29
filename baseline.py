## creator Junlin Lyu 2026
# baseline.py  v1 —— 连接数据库 + 抽取 schema
#
# 运行位置：服务器 C:\projects\insight-agent
# 运行方式：python baseline.py



import os
import duckdb
from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()

##配置导入
client = OpenAI(api_key=os.getenv("LLM_API_KEY"),
                base_url = os.getenv("LLM_BASE_URL"))

model = os.environ.get("LLM_MODEL", "deepseek-chat")

##链接数据库
con = duckdb.connect("data/olist.duckdb", read_only=True)
con.execute("SET MEMORY_LIMIT = '1GB'")
con.execute("SET threads = 2")
print("----数据库连接成功----")
print("    orders 行数:", con.execute("SELECT count(*) FROM orders").fetchone()[0])

##提取数据库的schema
def get_schema(con):
    ## 取出所有表以及他的type
    rows = con.execute("""
        select table_name, table_type
        from information_schema.tables
        where table_schema = 'main'
        order by table_type DESC, table_name""").fetchall()

    ##根据rows里所有表，生成他的表名 以及 他的type 和列 列属性
    parts = []
    for name, type in rows:
        cols = con.execute(f"DESCRIBE {name}").fetchall()
        coldef = ", ".join(f"{col[0]} {col[1]}"  for col in cols)
        parts.append(f"{type} {name} ({coldef})")

    return "\n".join(parts)

schema = get_schema(con)
print("\n----schema 抽取完成----")
print("    表/视图数量:", schema.count("\n") + 1)
print("    字符数:", len(schema))
print("    估算 token:", len(schema) // 2)

print("\n----schema 内容预览：")
print(schema[:800])


##创建prompt
q = "2018 年 8 月份的 GMV 是多少？"
system = f""" 你是一名资深的数据分析师，你可以把用户的中文问题翻译成DuckDB 的 SQL
数据库的结构和字段是：
{schema}

规则：
1. 只能输出一条SQL，不要解释，不要markdown 代码块
2. 只允许select
3. 数据的时间范围规定在 2016-09-04 到 2018-10-17
4. 一个订单可能有多条 order_items 记录，聚合时注意订单层级
5. price 是商品金额，freight_value 是运费


问题{q}

SQL：
"""

def build_prompt(schema, q):
    return system.format(schema, q)

##调用执行
def ask(q):
    response = client.chat.completions.create(

        model = model,
        messages = [{"role":"user", "content": build_prompt(schema, q)}],
        temperature = 0
    )
    return response.choices[0].message.content.strip(), response.usage


def clean_sql(text):
    text = text.replace("```sql", "").replace("```", "")
    return text.strip()



raw, usage = ask(q)
print("\n 模型原始输出：")
print(raw)

sql = clean_sql(raw)
print("\n 清洗后的 SQL：")
print(sql)

print("\n 执行结果：")
try:
    rows = con.execute(sql).fetchmany(10)
    print(rows)
except Exception as e:
    print("执行失败", str(e)[:300])

print("\n token：", usage.prompt_tokens, "->", usage.completion_tokens)



