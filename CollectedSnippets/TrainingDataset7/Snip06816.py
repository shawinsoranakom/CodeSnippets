def as_sql(self, compiler, connection, **extra_context):
        if (
            self.geo_field.geodetic(connection)
            and not connection.features.supports_length_geodetic
        ):
            raise NotSupportedError(
                "This backend doesn't support Length on geodetic fields"
            )
        return super().as_sql(compiler, connection, **extra_context)