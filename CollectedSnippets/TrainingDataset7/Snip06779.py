def from_db_value(self, value, expression, connection):
        return connection.ops.parse_raster(value)