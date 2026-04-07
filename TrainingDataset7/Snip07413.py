def z(self, value):
        "Set the Z component of the Point."
        if not self.hasz:
            raise GEOSException("Cannot set Z on 2D Point.")
        self._cs.setOrdinate(2, 0, value)