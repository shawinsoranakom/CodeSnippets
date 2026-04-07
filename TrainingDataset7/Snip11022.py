def select_format(self, compiler, sql, params):
        """
        Custom format for select clauses. For example, GIS columns need to be
        selected as AsText(table.col) on MySQL as the table.col data can't be
        used by Django.
        """
        return sql, params