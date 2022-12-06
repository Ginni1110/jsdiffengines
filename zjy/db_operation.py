#coding=utf-8
import sqlite3

#打开一个数据库，如果没有则会自动创建一个，
def get():
    conn = sqlite3.connect('top2000corpus-20200410-FX-SF.db')#在当前位置，创建（硬盘上）
    conn.execute('''CREATE TABLE IF NOT EXISTS Corpus(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    simple BLOB NOT NULL,
    used INTEGER default 0,

    UNIQUE(simple)
    );
''')
    print "Table created successfully";
    # 查找
    simples = conn.execute("select simple from Corpus limit 0,5000")
    print "Records created successfully";
    # 插入
    for(simple in simples):
        sql = f"INSERT OR IGNORE INTO Corpus (simple,used) VALUES"+"("+simple+","+0+")"
        conn.execute()
    conn.commit()
    print "Opened database successfully"

if __name__ == '__main__':
    get()