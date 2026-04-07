def z(self):
        "Return a list or numpy array of the Z variable."
        if not self.hasz:
            return None
        else:
            return self._listarr(self._cs.getZ)