##creator Junlin Lyu
##指标口径知识库：加载 / 匹配 / 渲染

import yaml
from pathlib import Path
import os

USE_HINT = os.environ.get("USE_HINT", "1") == "1"


met_path = Path("metrics.yml")

##加载全部指标
def read_metrics(path = None):
    p = Path(path) if path else met_path
    with open(p, encoding="utf-8") as f:
        return yaml.safe_load(f)["metrics"]


def match_metrics(question, metrics = None, top_k = 2):
    """两条规则：
      1. 最长别名优先 —— "复购间隔" 比 "复购" 具体，命中时后者让位
      2. top_k 限制 —— 防止一句话命中 4 条把 prompt 撑爆
    """
    metrics = metrics or read_metrics()
    q = question.lower()

    scored = []

    for metric in metrics:
        best = 0
        for word in metric["aliases"]:
            if word in q and len(word) > best:
                best = len(word)
        if best:
            scored.append([best, metric])

    scored.sort(key = lambda x: -x[0])

    seen, out = set(), list()
    for _, m in scored[:top_k]:
        if m["name"] in seen:
            continue
        seen.add(m["name"])
        out.append(m)
        if len(out) > top_k:
            break
    print(f"匹配metrics的结果为{out}")
    return out

##渲染成注入 prompt 的文本
def render_block(hits, max_chars = 1200):
    if not hits:
        print("hits为空，无法转换成prompt")
        return ""

    lines = ["【本问题涉及的指标口径，必须严格遵守】"]
    for m in hits:
        lines.append(f"\n指标：{m['name']}")
        lines.append(m["definition"].strip())
        if m.get("hint") and USE_HINT:
            lines.append("推荐写法：")
            lines.append(m["hint"].strip())

    block = "\n".join(lines)
    if len(block) > max_chars:
        block = block[:max_chars] + "\n（口径说明过长已截断）"
    return block

