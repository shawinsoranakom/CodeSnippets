def convert_value(self, value, expression, connection):
        return connection.ops.convert_extent(value)