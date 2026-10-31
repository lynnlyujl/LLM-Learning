import sys

import connect_db as db
from llm_predict import predict
from evaluate import evaluate_result
from read_cases import DEFAULT_CASES


def cmd_predict(tag, cases_path):
    con = db.connect()
    schema = db.get_schema(con)
    con.close()
    return predict(schema = schema, tag = tag, cases_path = cases_path)


def main():
    if len(sys.argv) < 2:
        print("用法:")
        print("  python main.py predict [tag] [cases]        生成预测 SQL（花钱）")
        print("  python main.py all     [tag] [cases]        predict + eval")
        print("  python main.py eval <pred.jsonl> [cases]    只评测（免费）")
        print()
        print("  cases 默认 cases.jsonl，可指定其他题库，例如 cases_holdout.jsonl")
        return

    cmd = sys.argv[1]

    if cmd == "predict":
        tag = sys.argv[2] if len(sys.argv) > 2 else "baseline"
        cases_path = sys.argv[3] if len(sys.argv) > 3 else DEFAULT_CASES
        cmd_predict(tag, cases_path)

    elif cmd == "all":
        tag = sys.argv[2] if len(sys.argv) > 2 else "baseline"
        cases_path = sys.argv[3] if len(sys.argv) > 3 else DEFAULT_CASES
        pred_path = cmd_predict(tag, cases_path)
        print(f"预测结果文件路径为{pred_path}")
        evaluate_result(str(pred_path))

    elif cmd == "eval":
        if len(sys.argv) < 3:
            print("需要指定预测文件: python main.py eval runs/xxx_pred.jsonl")
            return
        cases_path = sys.argv[4] if len(sys.argv) > 4 else None
        evaluate_result(sys.argv[2], cases_path)

    else:
        print(f"未知命令: {cmd}")


if __name__ == "__main__":
    main()