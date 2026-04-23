def as_sql(self, compiler, connection, **extra_context):
        if not connection.features.supports_area_geodetic and self.geo_field.geodetic(
            connection
        ):
            raise NotSupportedError(
                "Area on geodetic coordinate systems not supported."
            )
        return super().as_sql(compiler, connection, **extra_context)