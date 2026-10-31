##creator Junlin Lyu
##与gold结果进行比对测评

import json
import numbers
import datetime
from pathlib import Path

from read_cases import cases_by_id, DEFAULT_CASES
from connect_db import connect, run_query

##格式化单元格
def init_cell(cell):

    if cell is None:
        return ""
    if isinstance(cell, numbers.Number):
        return f"{float(cell):.6g}"
    if isinstance(cell, bool):
        return str(cell)
    return str(cell)

def init_is_num(cell):
    return isinstance(cell, numbers.Number) and not isinstance(cell, bool)

def _row_close(r1, r2, rel=1e-4):
    """逐值比较一行，数字用相对误差。"""
    if len(r1) != len(r2):
        return False
    for a, b in zip(r1, r2):
        if init_is_num(a) and init_is_num(b):
            a, b = float(a), float(b)
            # 相对容差：分母加 1e-12 防除零
            if abs(a - b) <= rel * max(abs(a), abs(b), 1e-12):
                continue
            return False
        else:
            if init_cell(a) != init_cell(b):
                return False
    return True

def init_row(rows):
    ans = []
    for row in rows:
        one_row = tuple(init_cell(cell) for cell in row)
        ans.append(one_row)


    return sorted(ans)

def compare(pred_rows, gold_rows):
    """返回 (是否相同, 不同原因)。原因用于归因。"""
    if len(pred_rows) != len(gold_rows):
        return False, f"行数不同 pred={len(pred_rows)} gold={len(gold_rows)}"
    if pred_rows and gold_rows and len(pred_rows[0]) != len(gold_rows[0]):
        return False, f"列数不同 pred={len(pred_rows[0])} gold={len(gold_rows[0])}"
    # 快路径：完全一致（含行顺序无关）
    if sorted(tuple(init_cell(v) for v in r) for r in pred_rows) == \
       sorted(tuple(init_cell(v) for v in r) for r in gold_rows):
        return True, ""
    remaining = list(gold_rows)
    for pr in pred_rows:
        for i, gr in enumerate(remaining):
            if _row_close(pr, gr):
                remaining.pop(i)
                break
        else:
            return False, "值不同（超出容差）"
    return (True, "") if not remaining else (False, "值不同（超出容差）")

def evaluate_result(pred_path, cases_path = None):
    pred_path = Path(pred_path)
    if not pred_path.exists():
        print(f"找不到路径文件 {pred_path}")
        return None

    with open(pred_path, encoding = "utf-8") as f:
        preds = [json.loads(line) for line in f if line.strip()]

    # 优先级：命令行参数 > 预测文件里记录的 > 默认
    if cases_path is None:
        cases_path = preds[0].get("cases_file", DEFAULT_CASES) if preds else DEFAULT_CASES

    con = connect()
    gold_map = cases_by_id(cases_path)

    print(f"预测文件: {pred_path.name}")
    print(f"用例文件: {cases_path}")

    with open(pred_path, encoding="utf-8") as f:
        preds = [json.loads(line) for line in f if line.strip()]

    pre_ids = {p["id"] for p in preds}
    missing = sorted(set(gold_map) - pre_ids)
    if missing:
        print(f"缺少用例{missing},准确率分母变小")

    print(f"文件: {pred_path.name}   用例数: {len(preds)}")
    print("=" * 30)

    records, passed = [], 0
    for p in preds:
        case = gold_map.get(p["id"])
        if not case:
            continue

        pred_sql = p.get("pred_sql")
        print(f"[{p['id']}] ({case['cat']}) {case['q']}")
        print(f"  SQL : {pred_sql}")

        try:
            gold_rows = run_query(con, case["gold"])
        except Exception as e:
            print(f"  !! gold 执行失败: {str(e)[:150]}")
            records.append({"id": p["id"], "cat": case["cat"],
                            "status": "GOLD_ERROR", "note": str(e)[:300]})
            continue

        try:
            pred_rows = run_query(con, pred_sql)
        except Exception as e:
            print(f"  执行失败: {str(e)[:150]}")
            records.append({"id": p["id"], "cat": case["cat"],
                            "status": "EXEC_ERROR", "q": case["q"],
                            "pred_sql": pred_sql, "note": str(e)[:300]})
            continue

        ok, reason = compare(pred_rows, gold_rows)
        passed += ok

        print(f"  gold: {gold_rows[:3]}")
        print(f"  pred: {pred_rows[:3]}")
        print(f"  结果: {'PASS' if ok else 'FAIL'}" + (f"  ({reason})" if reason else ""))

        records.append({
            "id": p["id"], "cat": case["cat"],
            "status": "PASS" if ok else "FAIL", "reason": reason,
            "q": case["q"], "pred_sql": pred_sql, "gold_sql": case["gold"],
            "gold": str(gold_rows[:5]), "pred": str(pred_rows[:5]),
        })

    total = len(records)
    gold_errors = sum(1 for r in records if r["status"] == "GOLD_ERROR")
    exec_errors = sum(1 for r in records if r["status"] == "EXEC_ERROR")
    evaluated = [r for r in records if r["status"] in ("PASS", "FAIL")]

    print("=" * 66)

    # 关键护栏：gold 全会挂时，拒绝给出准确率
    if not evaluated:
        print("!! 评测无效：所有用例的 gold SQL 都执行失败")
        print("   这不是模型的问题，是评测器或 gold 的问题。先修这个。")
        return None

    if gold_errors:
        print(f"!! 警告：{gold_errors} 条用例的 gold 执行失败，未计入准确率")

    acc = passed / len(evaluated)
    print(f"有效用例: {len(evaluated)}/{total}")
    print(f"执行准确率: {passed}/{len(evaluated)} = {acc:.0%}")
    if exec_errors:
        print(f"模型 SQL 执行失败: {exec_errors} 条")

    ans_dict = {}
    for record in records:
        ans_dict.setdefault(record["cat"], [0,0])
        ans_dict[record["cat"]][0] += (record["status"] == "PASS")
        ans_dict[record["cat"]][1] += 1
    for cat, (ok, n) in sorted(ans_dict.items()):
        print(f"  {cat:10s} {ok}/{n}")

    Path("runs").mkdir(exist_ok=True)
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    out = Path("runs") / f"{stamp}_report.json"
    out.write_text(json.dumps({
        "pred_file": str(pred_path), "passed": passed, "total": total,
        "by_cat": ans_dict, "records": records,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n已存档: {out}")
    return out