def requires_tiny_int(value):
            if value > 5:
                raise ValueError
            return value