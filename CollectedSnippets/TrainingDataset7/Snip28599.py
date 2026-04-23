def to_python(self, value):
                value = super().to_python(value)
                return value.split(",") if value else []