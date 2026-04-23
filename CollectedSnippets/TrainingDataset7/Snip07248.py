def is_counterclockwise(self):
        """Return whether this coordinate sequence is counterclockwise."""
        ret = c_byte()
        if not capi.cs_is_ccw(self.ptr, byref(ret)):
            raise GEOSException(
                'Error encountered in GEOS C function "%s".' % capi.cs_is_ccw.func_name
            )
        return ret.value == 1