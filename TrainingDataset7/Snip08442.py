def open(self, mode=None, *args, **kwargs):
        if not self.closed:
            self.seek(0)
        elif self.name and os.path.exists(self.name):
            self.file = open(self.name, mode or self.mode, *args, **kwargs)
        else:
            raise ValueError("The file cannot be reopened.")
        return self