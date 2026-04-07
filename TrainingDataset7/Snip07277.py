def dims(self):
        "Return the dimension of this Geometry (0=point, 1=line, 2=surface)."
        return capi.get_dims(self.ptr)