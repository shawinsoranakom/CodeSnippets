def to_python(self, value):
        if value in self.empty_values:
            return ""
        value = value.strip()
        if value and ":" in value:
            return clean_ipv6_address(
                value, self.unpack_ipv4, max_length=self.max_length
            )
        return value