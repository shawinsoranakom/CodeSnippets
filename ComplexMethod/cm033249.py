def add_kb_filter(sql):
        # Add kb_id filter for ES/OS only (Infinity already has it in table name)
        if doc_engine == "infinity" or not kb_ids:
            return sql

        # Build kb_filter: single KB or multiple KBs with OR
        if len(kb_ids) == 1:
            kb_filter = f"kb_id = '{kb_ids[0]}'"
        else:
            kb_filter = "(" + " OR ".join([f"kb_id = '{kb_id}'" for kb_id in kb_ids]) + ")"

        if "where " not in sql.lower():
            o = sql.lower().split("order by")
            if len(o) > 1:
                sql = o[0] + f" WHERE {kb_filter}  order by " + o[1]
            else:
                sql += f" WHERE {kb_filter}"
        elif "kb_id =" not in sql.lower() and "kb_id=" not in sql.lower():
            sql = re.sub(r"\bwhere\b ", f"where {kb_filter} and ", sql, flags=re.IGNORECASE)
        return sql