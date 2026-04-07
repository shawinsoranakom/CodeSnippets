def lower_case_function_super(self, compiler, connection):
            self.extra["function"] = self.function.lower()
            return super(MySum, self).as_sql(compiler, connection)