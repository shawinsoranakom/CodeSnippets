def ensure_file(self, path):
        path.parent.mkdir(exist_ok=True, parents=True)
        path.touch()
        # On Linux and Windows updating the mtime of a file using touch() will
        # set a timestamp value that is in the past, as the time value for the
        # last kernel tick is used rather than getting the correct absolute
        # time.
        # To make testing simpler set the mtime to be the observed time when
        # this function is called.
        self.set_mtime(path, time.time())
        return path.absolute()