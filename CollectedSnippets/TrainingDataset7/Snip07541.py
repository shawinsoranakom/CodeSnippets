def check_srs(self, source_srs):
        "Check the compatibility of the given spatial reference object."

        if isinstance(source_srs, SpatialReference):
            sr = source_srs
        elif isinstance(source_srs, self.spatial_backend.spatial_ref_sys()):
            sr = source_srs.srs
        elif isinstance(source_srs, (int, str)):
            sr = SpatialReference(source_srs)
        else:
            # Otherwise just pulling the SpatialReference from the layer
            sr = self.layer.srs

        if not sr:
            raise LayerMapError("No source reference system defined.")
        else:
            return sr