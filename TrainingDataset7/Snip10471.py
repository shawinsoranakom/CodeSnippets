def serialize(self):
        return repr(os.fspath(self.value)), {}