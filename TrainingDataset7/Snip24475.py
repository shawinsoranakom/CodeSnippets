def has_spatial_indexes(self):
        if connection.ops.mysql:
            with connection.cursor() as cursor:
                return connection.introspection.supports_spatial_index(
                    cursor, "gis_neighborhood"
                )
        return True