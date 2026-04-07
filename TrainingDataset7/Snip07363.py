def y(self):
        "Return a list or numpy array of the Y variable."
        return self._listarr(self._cs.getY)