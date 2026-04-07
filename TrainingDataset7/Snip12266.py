def build_where(self, filter_expr):
        return self.build_filter(filter_expr, allow_joins=False)[0]