def to_asgi_names(cls, headers):
        return {
            cls.to_asgi_name(header_name): value
            for header_name, value in headers.items()
        }