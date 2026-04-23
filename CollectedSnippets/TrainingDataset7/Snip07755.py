def decompress(self, value):
        if value:
            return (value.lower, value.upper)
        return (None, None)