def num_coords(self):
        "Return the number of coordinates in the Geometry."
        return capi.get_num_coords(self.ptr)