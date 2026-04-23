def has_spatial_indexes(self, table):
        if connection.ops.mysql:
            with connection.cursor() as cursor:
                return connection.introspection.supports_spatial_index(cursor, table)
        elif connection.ops.oracle:
            # Spatial indexes in Meta.indexes are not supported by the Oracle
            # backend (see #31252).
            return False
        return True