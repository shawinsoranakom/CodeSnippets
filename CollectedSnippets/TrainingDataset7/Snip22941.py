def to_python(self, value):
                # Fake json.loads
                if value == "{}":
                    return {}
                return super().to_python(value)