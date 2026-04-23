def as_oracle(self, compiler, connection, **extra_context):
        return super().as_sql(
            compiler, connection, function="DBMS_RANDOM.VALUE", **extra_context
        )