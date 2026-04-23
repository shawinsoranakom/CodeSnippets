def to_python(self, value):
        if not value:
            return
        if not isinstance(value, MyWrapper):
            value = MyWrapper(value)
        return value