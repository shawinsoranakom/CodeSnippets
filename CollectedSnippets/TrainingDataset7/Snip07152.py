def clone(self):
        "Return a clone of this SpatialReference object."
        return SpatialReference(capi.clone_srs(self.ptr), axis_order=self.axis_order)