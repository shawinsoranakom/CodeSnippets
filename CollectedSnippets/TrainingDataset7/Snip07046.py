def srs(self):
        "Return the Spatial Reference used in this Layer."
        try:
            ptr = capi.get_layer_srs(self.ptr)
            return SpatialReference(srs_api.clone_srs(ptr))
        except SRSException:
            return None