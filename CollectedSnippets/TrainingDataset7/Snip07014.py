def x(self):
        "Return the X coordinates in a list."
        return self._listarr(capi.getx)