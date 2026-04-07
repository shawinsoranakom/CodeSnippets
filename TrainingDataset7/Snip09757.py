def quote_value(self, value):
        if isinstance(value, (datetime.date, datetime.time, datetime.datetime)):
            return "'%s'" % value
        elif isinstance(value, datetime.timedelta):
            return "'%s'" % duration_iso_string(value)
        elif isinstance(value, str):
            return "'%s'" % value.replace("'", "''")
        elif isinstance(value, (bytes, bytearray, memoryview)):
            return "'%s'" % value.hex()
        elif isinstance(value, bool):
            return "1" if value else "0"
        else:
            return str(value)