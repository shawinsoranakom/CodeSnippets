def close(self):
        file = getattr(self, "_file", None)
        if file is not None:
            file.close()