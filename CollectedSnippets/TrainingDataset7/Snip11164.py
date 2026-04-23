def to_python(self, value):
        if value is None:
            return None
        if not isinstance(value, str):
            value = str(value)
        value = value.strip()
        if ":" in value:
            return clean_ipv6_address(
                value, self.unpack_ipv4, self.error_messages["invalid"]
            )
        return value