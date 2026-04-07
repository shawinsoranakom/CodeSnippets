def y(self):
        "Return the Y coordinate for this Point."
        return capi.gety(self.ptr, 0)