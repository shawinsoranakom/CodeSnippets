def coord_dim(self):
        "Return the coordinate dimension of the Geometry."
        return capi.get_coord_dim(self.ptr)