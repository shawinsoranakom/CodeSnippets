def m(self):
        """Return the M coordinates in a list."""
        if self.is_measured:
            return self._listarr(capi.getm)