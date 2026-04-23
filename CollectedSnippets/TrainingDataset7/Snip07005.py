def x(self):
        "Return the X coordinate for this Point."
        return capi.getx(self.ptr, 0)