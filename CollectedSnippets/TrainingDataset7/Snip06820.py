def as_sqlite(self, compiler, connection, **extra_context):
        if self.geo_field.geodetic(connection):
            raise NotSupportedError("Perimeter cannot use a non-projected field.")
        return super().as_sql(compiler, connection, **extra_context)