def m(self):
        """Return the M coordinate for this Point."""
        if self.is_measured:
            return capi.getm(self.ptr, 0)