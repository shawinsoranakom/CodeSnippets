def to_url(self, value):
        return base64.b64encode(value).decode("ascii")