def num_geom(self):
        "Return the number of geometries in the Geometry."
        return capi.get_num_geoms(self.ptr)