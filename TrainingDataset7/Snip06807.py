def as_sqlite(self, compiler, connection, **extra_context):
        if self.geo_field.geodetic(connection):
            # SpatiaLite returns NULL instead of zero on geodetic coordinates
            extra_context["template"] = (
                "COALESCE(%(function)s(%(expressions)s, %(spheroid)s), 0)"
            )
            extra_context["spheroid"] = int(bool(self.spheroid))
        return super().as_sql(compiler, connection, **extra_context)