def process_rhs(self, compiler, connection):
        if self.rhs_is_direct_value():
            # rhs should be an iterable of values. Use batch_process_rhs()
            # to prepare/transform those values.
            return self.batch_process_rhs(compiler, connection)
        elif isinstance(self.rhs, ExpressionList):
            # rhs contains at least one expression. Unwrap them and delegate
            # to batch_process_rhs() to prepare/transform those values.
            copy = self.copy()
            copy.rhs = self.rhs.get_source_expressions()
            return copy.process_rhs(compiler, connection)
        else:
            return super().process_rhs(compiler, connection)