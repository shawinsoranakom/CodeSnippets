def as_sqlite(self, compiler, connection, **extra_context):
        sql, params = self.as_sql(compiler, connection, **extra_context)
        try:
            if self.output_field.get_internal_type() == "DecimalField":
                if isinstance(self.value, Decimal):
                    sql = "(CAST(%s AS REAL))" % sql
                else:
                    sql = "(CAST(%s AS NUMERIC))" % sql
        except FieldError:
            pass
        return sql, params