def be_evil(self, compiler, connection):
            substitutions = {
                "function": "MAX",
                "expressions": "2",
                "distinct": "",
                "filter": "",
                "order_by": "",
            }
            substitutions.update(self.extra)
            return self.template % substitutions, ()