import sqlite3

class UnifiedCursor:
    def __init__(self, cursor, engine):
        self.cursor = cursor
        self.engine = engine
        self.lastrowid = None
        
    def execute(self, sql, params=()):
        if self.engine == "POSTGRES":
            sql_conv = sql.replace("?", "%s")
            # If insert without returning id
            is_insert = sql_conv.strip().upper().startswith("INSERT INTO")
            if is_insert and "RETURNING" not in sql_conv.upper():
                sql_conv += " RETURNING id"
                self.cursor.execute(sql_conv, params)
                res = self.cursor.fetchone()
                self.lastrowid = res[0] if res else None
                return self
            self.cursor.execute(sql_conv, params)
            return self
        else:
            self.cursor.execute(sql, params)
            self.lastrowid = self.cursor.lastrowid
            return self

    def fetchone(self):
        return self.cursor.fetchone()
        
    def fetchall(self):
        return self.cursor.fetchall()

# Test with sqlite
conn = sqlite3.connect(":memory:")
conn.row_factory = sqlite3.Row
c = UnifiedCursor(conn.cursor(), "SQLITE")
c.execute("CREATE TABLE t (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT)")
c.execute("INSERT INTO t (name) VALUES (?)", ("Test",))
print("Lastrowid:", c.lastrowid)
c.execute("SELECT * FROM t WHERE name = ?", ("Test",))
row = c.fetchone()
print("Row name:", row["name"])
conn.close()
