def quote_value(self, value):
        if isinstance(value, self.connection.ops.Adapter):
            return super().quote_value(str(value))
        return super().quote_value(value)