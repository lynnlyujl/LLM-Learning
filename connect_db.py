##creator Junlin Lyu
##链接数据库


import duckdb

DB_PATH = "data/olist.duckdb"

con = duckdb.connect("data/olist.duckdb", read_only=True)
con.execute("SET MEMORY_LIMIT = '1GB'")
con.execute("SET threads = 2")
print("----数据库连接成功----")
print("    orders 行数:", con.execute("SELECT count(*) FROM orders").fetchone()[0])

##链接数据库
def connect(path = DB_PATH):
    con = duckdb.connect("data/olist.duckdb", read_only=True)
    con.execute("SET MEMORY_LIMIT = '1GB'")
    con.execute("SET threads = 2")
    return con


##运行sql通用方法
def run_query(con, query, limit = 100):
    return con.execute(query).fetchmany(limit)


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