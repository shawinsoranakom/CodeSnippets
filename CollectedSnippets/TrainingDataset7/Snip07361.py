def array(self):
        "Return a numpy array for the LineString."
        return self._listarr(self._cs.__getitem__)