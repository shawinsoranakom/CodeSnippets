def quote_value(self, value):
        self.connection.ensure_connection()
        # MySQLdb escapes to string, PyMySQL to bytes.
        quoted = self.connection.connection.escape(
            value, self.connection.connection.encoders
        )
        if isinstance(value, str) and isinstance(quoted, bytes):
            quoted = quoted.decode()
        return quoted