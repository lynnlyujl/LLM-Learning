##creator Junlin Lyu
##读取case

import json
from pathlib import Path

case_path = Path("cases.jsonl")

##读取case json中的case
def load_cases(path = None):
    p = Path(path) if path else case_path
    with open(p, encoding="utf-8") as f:
        # 逐行解析：每行是一个独立 JSON
        # if line.strip() 跳过空行，防止文件末尾多一个换行导致崩溃
        return [json.loads(line) for line in f if line.strip()]
        ##返回 [{id, cat, q, gold}, ...]，按文件中的顺序

## 把case中的id 提取出来
def cases_by_id(path =  None):
    ##返回 {id: case}，评测时按 id 把预测和用例对齐
    return {c["id"]: c for c in load_cases(path)}
