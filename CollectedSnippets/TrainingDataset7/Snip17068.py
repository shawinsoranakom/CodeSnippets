def as_sql(self, compiler, connection):
                self.set_source_expressions(self.get_source_expressions()[0:1])
                return super().as_sql(compiler, connection)