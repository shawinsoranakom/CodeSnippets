def __init__(self, mode="w+b", bufsize=-1, suffix="", prefix="", dir=None):
            fd, name = tempfile.mkstemp(suffix=suffix, prefix=prefix, dir=dir)
            self.name = name
            self.file = os.fdopen(fd, mode, bufsize)
            self.close_called = False