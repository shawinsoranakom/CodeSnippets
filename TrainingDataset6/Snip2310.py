def _expanduser(self):
    return self.__class__(os.path.expanduser(str(self)))