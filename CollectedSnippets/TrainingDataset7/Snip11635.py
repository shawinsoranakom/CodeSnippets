def process_lhs(self, compiler, connection, lhs=None):
        sql, params = super().process_lhs(compiler, connection, lhs)
        if not isinstance(self.lhs, Tuple):
            sql = f"({sql})"
        return sql, params