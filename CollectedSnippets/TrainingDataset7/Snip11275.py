def closed(self):
        file = getattr(self, "_file", None)
        return file is None or file.closed