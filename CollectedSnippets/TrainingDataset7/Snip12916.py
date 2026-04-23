def to_wsgi_names(cls, headers):
        return {
            cls.to_wsgi_name(header_name): value
            for header_name, value in headers.items()
        }