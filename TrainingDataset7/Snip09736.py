def process_clob(self, value):
        if value is None:
            return ""
        return value.read()