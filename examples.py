##creator Junlin Lyu
##few-shot 样例库：加载 / 检索 / 渲染
##
##为什么手写 TF-IDF 而不用 sklearn：
##  1. 只为这件事装 30MB 的 scikit-learn 不值得
##  2. 只有 8 条文档，TF-IDF 和向量检索没有可测差异
##  3. 手写一遍能讲清原理 —— 面试问"你用的什么相似度"要答得出来

import re
import numpy as np
import yaml
from pathlib import Path

EXAMPLES_PATH = Path("examples.yml")
_INDEX = None          ##第一次检索时构建，之后复用


##加载样例
def load_examples(path = None):
    p = Path(path) if path else EXAMPLES_PATH
    with open(p, encoding = "utf-8") as f:
        return yaml.safe_load(f)["examples"]


##字符 n-gram
def _grams(text, ns = (2, 3)):
    """为什么用字符 n-gram 而不是分词：
       中文分词需要额外依赖（jieba），而 '复购率' 的 bigram
       就是 '复购' / '购率'，本身已经很有效。
    """
    t = re.sub(r"[\s\W_]+", "", text.lower())     ##去掉空白和标点
    out = {}
    for n in ns:
        for i in range(len(t) - n + 1):
            g = t[i:i + n]
            out[g] = out.get(g, 0) + 1
    return out


##构建 TF-IDF 矩阵（8 条文档，秒级完成）
def _build_index(docs):
    grams = [_grams(d) for d in docs]

    ##建词表
    vocab = {}
    for g in grams:
        for k in g:
            if k not in vocab:
                vocab[k] = len(vocab)

    ##IDF：越罕见的 n-gram 权重越高
    df = np.zeros(len(vocab))
    for g in grams:
        for k in set(g):
            df[vocab[k]] += 1
    idf = np.log((1 + len(docs)) / (1 + df)) + 1

    ##TF-IDF 矩阵
    mat = np.zeros((len(docs), len(vocab)))
    for i, g in enumerate(grams):
        total = sum(g.values()) or 1
        for k, c in g.items():
            mat[i, vocab[k]] = (c / total) * idf[vocab[k]]

    ##L2 归一化：这样点积就等于余弦相似度
    norms = np.linalg.norm(mat, axis = 1, keepdims = True)
    norms[norms == 0] = 1
    return vocab, idf, mat / norms


def _get_index(examples):
    global _INDEX
    if _INDEX is None:
        # 只用「问题 + 关键词」建索引
        # 不含 note 和 sql：note 里的"评价""订单"等通用词会造成跨类误召回
        docs = [
            e["q"] + " " + " ".join(e.get("keywords", []))
            for e in examples
        ]
        _INDEX = _build_index(docs)
    return _INDEX


##检索最相似的前 k 条样例
def retrieve(question, examples = None, k = 2, min_score = 0.05):
    """min_score 是保底阈值：
       相似度太低就不注入，避免往 prompt 里塞无关内容（上下文噪声）。
    """
    examples = examples or load_examples()
    vocab, idf, mat = _get_index(examples)

    qg = _grams(question)
    qv = np.zeros(len(vocab))
    total = sum(qg.values()) or 1
    for g, c in qg.items():
        if g in vocab:
            qv[vocab[g]] = (c / total) * idf[vocab[g]]

    n = np.linalg.norm(qv)
    if n == 0:
        return []
    qv = qv / n

    scores = mat @ qv
    out = []
    for i in scores.argsort()[::-1][:k]:
        if scores[i] < min_score:
            break
        out.append((examples[i], float(scores[i])))
    return out


##渲染成注入 prompt 的文本
def render_examples(hits, max_chars = 1500):
    if not hits:
        return ""
    lines = ["【参考示例：类似问题的正确 SQL 写法】"]
    for i, (ex, score) in enumerate(hits, 1):
        lines.append(f"\n示例{i}（{ex.get('cat', '')}）：{ex['q']}")
        lines.append(ex["sql"].strip())
        if ex.get("note"):
            lines.append("说明：" + ex["note"].strip())

    block = "\n".join(lines)
    if len(block) > max_chars:
        block = block[:max_chars] + "\n（示例过长已截断）"
    return block