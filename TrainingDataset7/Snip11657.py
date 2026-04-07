def as_oracle(self, compiler, connection, **extra_context):
        if self.output_field.get_internal_type() == "JSONField":
            # Oracle doesn't support explicit cast to JSON.
            template = "JSON_QUERY(%(expressions)s, '$')"
            return super().as_sql(
                compiler, connection, template=template, **extra_context
            )
        return self.as_sql(compiler, connection, **extra_context)