def z(self):
        "Return the Z coordinate for this Point."
        if self.is_3d:
            return capi.getz(self.ptr, 0)