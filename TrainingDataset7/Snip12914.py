def to_wsgi_name(cls, header):
        header = header.replace("-", "_").upper()
        if header in cls.UNPREFIXED_HEADERS:
            return header
        return f"{cls.HTTP_PREFIX}{header}"