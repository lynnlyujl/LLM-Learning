import os
from dotenv import load_dotenv
from openai import OpenAI

##加载配置文件
load_dotenv()

##简历客户端 读取对应配置文件中内容
client = OpenAI(api_key=os.getenv("LLM_API_KEY"),
                base_url=os.getenv("LLM_BASE_URL"))


##选择模型
MODEL = os.environ.get("LLM_MODEL", "deepseek-chat")


##发一次最小请求 测试是否连通

resp = client.chat.completions.create(
    model = MODEL,
    messages = [{"role": "user", "content": "测试已连通，收到消息"}]
)

##查看结果

#查看结果前可以打印响应
print("相应内容为：")
print(resp.model_dump())
print("收到结果：")
print(resp.choices[0].message.content)



##统计token
print("tokens", resp.usage.prompt_tokens, "->", resp.usage.completion_tokens)
