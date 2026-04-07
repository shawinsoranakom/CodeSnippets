def as_mysql(self, compiler, connection, **extra_context):
        template = None
        output_type = self.output_field.get_internal_type()
        # MySQL doesn't support explicit cast to float.
        if output_type == "FloatField":
            template = "(%(expressions)s + 0.0)"
        # MariaDB doesn't support explicit cast to JSON.
        elif output_type == "JSONField" and connection.mysql_is_mariadb:
            template = "JSON_EXTRACT(%(expressions)s, '$')"
        return self.as_sql(compiler, connection, template=template, **extra_context)