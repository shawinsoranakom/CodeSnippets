def geom(self):
        "Return the OGR Geometry for this Feature."
        # Retrieving the geometry pointer for the feature.
        geom_ptr = capi.get_feat_geom_ref(self.ptr)
        return OGRGeometry(geom_api.clone_geom(geom_ptr))