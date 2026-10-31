##creator Junlin Lyu
##llm运行


import json
import datetime
from pathlib import Path

from read_cases import load_cases, DEFAULT_CASES
from llm_running import ask, clean_sql, model

from metrics import match_metrics, render_block
from examples import retrieve, render_examples

##预测函数
def predict(schema, tag = "baseline", cases_path = DEFAULT_CASES):
    cases = load_cases(cases_path)
    rows = []
    print(f"用例文件: {cases_path}")
    print(f"用例数: {len(cases)}  模型: {model}")
    print("=" * 30)

    for i in cases:
        block = render_block(match_metrics(i["q"]))
        mblock = render_block(match_metrics(i["q"]))
        raw, usage = ask(schema, i["q"], block, mblock)

        sql = clean_sql(raw)


        rows.append({
            "id": i["id"],
            "cat": i["cat"],
            "q": i["q"],
            "pred_sql":sql,
            "prompt_tokens":usage.prompt_tokens,
            "completion_tokens":usage.completion_tokens,
            "cases_file": cases_path
        })
        print(f"[{i['id']}] {i['q']}")
        print(f"     {sql[:150]}")

    ## 建立结果存储，以及每次结果需要有时间戳
    Path("runs").mkdir(exist_ok=True)
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M")
    out = Path("runs") / f"{stamp}_{tag}_pred.jsonl"

    with open(out, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    ##统计token
    total_out = sum(r["completion_tokens"] for r in rows)
    total_in = sum(r["prompt_tokens"] for r in rows)
    print("=" * 30)
    print(f"tokens: {total_in} 入 / {total_out} 出")
    print(f"已写入: {out}")
    return out

