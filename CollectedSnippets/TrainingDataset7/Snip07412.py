def z(self):
        "Return the Z component of the Point."
        return self._cs.getOrdinate(2, 0) if self.hasz else None