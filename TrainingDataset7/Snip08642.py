def __enter__(self):
        try:
            self.open()
        except Exception:
            self.close()
            raise
        return self