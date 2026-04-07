def decompress(self, value):
        if value:
            return value.split("__")
        return ["", ""]