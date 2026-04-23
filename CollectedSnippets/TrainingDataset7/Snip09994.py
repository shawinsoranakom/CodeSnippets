def _get_column_collations(self, cursor, table_name):
        row = cursor.execute(
            """
            SELECT sql
            FROM sqlite_master
            WHERE type = 'table' AND name = %s
        """,
            [table_name],
        ).fetchone()
        if not row:
            return {}

        sql = row[0]
        columns = str(sqlparse.parse(sql)[0][-1]).strip("()").split(", ")
        collations = {}
        for column in columns:
            tokens = column[1:].split()
            column_name = tokens[0].strip('"')
            for index, token in enumerate(tokens):
                if token == "COLLATE":
                    collation = tokens[index + 1]
                    break
            else:
                collation = None
            collations[column_name] = collation
        return collations