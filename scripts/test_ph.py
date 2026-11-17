import re

def convert_placeholders(sql, engine):
    if engine == "POSTGRES":
        # Convert ? to %s
        return sql.replace("?", "%s")
    return sql

print("Placeholder test:", convert_placeholders("SELECT * FROM t WHERE a = ? AND b = ?", "POSTGRES"))
