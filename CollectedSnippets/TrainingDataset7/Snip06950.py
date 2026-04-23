def dimension(self):
        "Return 0 for points, 1 for lines, and 2 for surfaces."
        return capi.get_dims(self.ptr)