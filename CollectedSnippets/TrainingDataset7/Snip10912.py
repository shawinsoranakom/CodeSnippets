def get_group_by_cols(self):
        group_by_cols = []
        for expr in self.get_source_expressions():
            group_by_cols.extend(expr.get_group_by_cols())
        return group_by_cols