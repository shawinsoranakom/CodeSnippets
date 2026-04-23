def from_db_value(self, value, expression, connection):
        cash = Cash(value)
        cash.vendor = connection.vendor
        return cash