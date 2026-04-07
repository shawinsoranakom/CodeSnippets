def quote_value(self, value):
        return sql.quote(value, self.connection.connection)