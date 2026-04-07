def set_source_expressions(self, exprs):
        *exprs, self.filter, self.order_by = exprs
        return super().set_source_expressions(exprs)