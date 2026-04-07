def trim(self, flag):
        if bool(flag) != self._trim:
            self._trim = bool(flag)
            wkt_writer_set_trim(self.ptr, self._trim)