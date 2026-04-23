def to_python(self, value):
        return base64.b64decode(value)