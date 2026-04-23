def __repr__(self):
        return "<%s: %s>" % (
            self.__class__.__name__,
            os.sep.join([self.dirpath, self.file]),
        )