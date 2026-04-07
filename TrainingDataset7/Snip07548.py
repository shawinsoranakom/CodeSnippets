def coord_transform(self):
        "Return the coordinate transformation object."
        SpatialRefSys = self.spatial_backend.spatial_ref_sys()
        try:
            # Getting the target spatial reference system
            target_srs = (
                SpatialRefSys.objects.using(self.using)
                .get(srid=self.geo_field.srid)
                .srs
            )

            # Creating the CoordTransform object
            return CoordTransform(self.source_srs, target_srs)
        except Exception as exc:
            raise LayerMapError(
                "Could not translate between the data source and model geometry."
            ) from exc