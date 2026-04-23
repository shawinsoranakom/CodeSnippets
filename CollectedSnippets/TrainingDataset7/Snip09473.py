def __init__(self, table, expressions, compiler, quote_value):
        self.compiler = compiler
        self.expressions = expressions
        self.quote_value = quote_value
        columns = [
            col.target.column
            for col in self.compiler.query._gen_cols([self.expressions])
        ]
        super().__init__(table, columns)