def x(self):
        "Return a list or numpy array of the X variable."
        return self._listarr(self._cs.getX)