def _get_index_columns_orders(self, sql):
        tokens = sqlparse.parse(sql)[0]
        for token in tokens:
            if isinstance(token, sqlparse.sql.Parenthesis):
                columns = str(token).strip("()").split(", ")
                return ["DESC" if info.endswith("DESC") else "ASC" for info in columns]
        return None