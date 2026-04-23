def _quote(value, connection=None):
        adapted = extensions.adapt(value)
        if hasattr(adapted, "encoding"):
            adapted.encoding = "utf8"
        # getquoted() returns a quoted bytestring of the adapted value.
        return adapted.getquoted().decode()