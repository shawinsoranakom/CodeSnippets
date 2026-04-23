def batch_process_rhs(self, compiler, connection, rhs=None):
        pre_processed = super().batch_process_rhs(compiler, connection, rhs)
        # The params list may contain expressions which compile to a
        # sql/param pair. Zip them to get sql and param pairs that refer to the
        # same argument and attempt to replace them with the result of
        # compiling the param step.
        sql, params = zip(
            *(
                self.resolve_expression_parameter(compiler, connection, sql, param)
                for sql, param in zip(*pre_processed)
            )
        )
        params = itertools.chain.from_iterable(params)
        return sql, tuple(params)