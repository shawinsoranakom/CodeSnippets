def get_converters(self, expressions):
        i = 0
        converters = {}

        for expression in expressions:
            if isinstance(expression, ColPairs):
                cols = expression.get_source_expressions()
                cols_converters = self.get_converters(cols)
                for j, (convs, col) in cols_converters.items():
                    converters[i + j] = (convs, col)
                i += len(expression)
            elif expression:
                backend_converters = self.connection.ops.get_db_converters(expression)
                field_converters = expression.get_db_converters(self.connection)
                if backend_converters or field_converters:
                    converters[i] = (backend_converters + field_converters, expression)
                i += 1
            else:
                i += 1

        return converters