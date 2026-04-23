def lower_case_function_override(self, compiler, connection):
            sql, params = compiler.compile(self.source_expressions[0])
            substitutions = {
                "function": self.function.lower(),
                "expressions": sql,
                "distinct": "",
                "filter": "",
                "order_by": "",
            }
            substitutions.update(self.extra)
            return self.template % substitutions, params