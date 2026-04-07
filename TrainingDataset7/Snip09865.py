def adapt_ipaddressfield_value(self, value):
        if value:
            return Inet(value)
        return None