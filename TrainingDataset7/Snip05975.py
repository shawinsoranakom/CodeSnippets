def format_value(self, value):
        return ",".join(str(v) for v in value) if value else ""