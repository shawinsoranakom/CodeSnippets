def as_sql(self, compiler, connection, **extra_context):
        extra_context["db_type"] = self.output_field.cast_db_type(connection)
        return super().as_sql(compiler, connection, **extra_context)