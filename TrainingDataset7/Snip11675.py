def as_oracle(self, compiler, connection, **extra_context):
        return self.as_sql(
            compiler, connection, template="LOCALTIMESTAMP", **extra_context
        )