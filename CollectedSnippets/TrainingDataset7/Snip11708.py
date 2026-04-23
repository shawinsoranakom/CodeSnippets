def as_mysql(self, compiler, connection, **extra_context):
        sql, params = super().as_sql(compiler, connection, **extra_context)
        if self.output_field.get_internal_type() == "DurationField":
            sql = "CAST(%s AS SIGNED)" % sql
        return sql, params