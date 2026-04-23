def get_db_prep_value(self, value, connection, prepared=False):
        value = super().get_db_prep_value(value, connection, prepared)
        return connection.ops.adapt_decimalfield_value(
            self.to_python(value), self.max_digits, self.decimal_places
        )