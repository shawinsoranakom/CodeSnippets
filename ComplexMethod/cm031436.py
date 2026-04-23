def shouldRollover(self, record):
        """
        Determine if rollover should occur.

        Basically, see if the supplied record would cause the file to exceed
        the size limit we have.
        """
        if self.stream is None:                 # delay was set...
            self.stream = self._open()
        if self.maxBytes > 0:                   # are we rolling over?
            try:
                pos = self.stream.tell()
            except io.UnsupportedOperation:
                # gh-143237: Never rollover a named pipe.
                return False
            if not pos:
                # gh-116263: Never rollover an empty file
                return False
            msg = "%s\n" % self.format(record)
            if pos + len(msg) >= self.maxBytes:
                # See bpo-45401: Never rollover anything other than regular files
                if os.path.exists(self.baseFilename) and not os.path.isfile(self.baseFilename):
                    return False
                return True
        return False