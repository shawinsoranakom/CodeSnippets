def _set_byteorder(self, order):
        if order not in (0, 1):
            raise ValueError(
                "Byte order parameter must be 0 (Big Endian) or 1 (Little Endian)."
            )
        wkb_writer_set_byteorder(self.ptr, order)