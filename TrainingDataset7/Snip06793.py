def as_sqlite(self, compiler, connection, **extra_context):
        if self.geo_field.geodetic(connection):
            extra_context["template"] = "%(function)s(%(expressions)s, %(spheroid)d)"
            extra_context["spheroid"] = True
        return self.as_sql(compiler, connection, **extra_context)