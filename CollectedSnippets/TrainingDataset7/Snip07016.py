def z(self):
        "Return the Z coordinates in a list."
        if self.is_3d:
            return self._listarr(capi.getz)