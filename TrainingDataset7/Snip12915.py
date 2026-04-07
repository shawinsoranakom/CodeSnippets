def to_asgi_name(cls, header):
        return header.replace("-", "_").upper()