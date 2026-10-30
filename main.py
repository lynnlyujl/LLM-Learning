import sys

import connect_db as db
from llm_predict import predict
from evaluate import evaluate_result


def cmd_predict(tag):
    # 连库、拿 schema —— 这是唯一需要数据库的步骤
    con = db.connect()
    schema = db.get_schema(con)
    con.close()
    pred_path = predict(schema=schema, tag=tag)
    return pred_path

def main():
    if len(sys.argv) < 2 and sys.argv[1] != "all":
        print("用法:")
        print("  python main.py predict [tag]        生成预测 SQL（花 API 钱）")
        print("  python main.py eval <pred.jsonl>    评测（免费，可重跑）")
        return

    cmd = sys.argv[1]

    if cmd == "predict":
        tag = sys.argv[2] if len(sys.argv) > 2 else "baseline"
        cmd_predict(tag)
    elif cmd == "eval":
        if len(sys.argv) < 3:
            print("需要指定预测文件: python main.py eval runs/xxx_pred.jsonl")
            return
        print(f"预测结果文件路径为{sys.argv[2]}")
        evaluate_result(sys.argv[2])
    elif cmd == "all":
        tag = sys.argv[2] if len(sys.argv) > 2 else "baseline"
        pred_path = cmd_predict(tag)
        print(f"预测结果文件路径为{pred_path}")
        evaluate_result(str(pred_path))
    else:
        print(f"未知命令: {cmd}")


if __name__ == "__main__":
    main()

