def to_python(self, value):
        if isinstance(value, Team):
            return value
        return Team(value)