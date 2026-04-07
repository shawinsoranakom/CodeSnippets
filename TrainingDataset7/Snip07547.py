def verify_geom(self, geom, model_field):
        """
        Verify the geometry -- construct and return a GeometryCollection
        if necessary (for example if the model field is MultiPolygonField while
        the mapped shapefile only contains Polygons).
        """
        # Measured geometries are not yet supported by GeoDjango models.
        if geom.is_measured:
            geom.set_measured(False)

        # Downgrade a 3D geom to a 2D one, if necessary.
        if self.coord_dim == 2 and geom.is_3d:
            geom.set_3d(False)

        if self.make_multi(geom.geom_type, model_field):
            # Constructing a multi-geometry type to contain the single geometry
            multi_type = self.MULTI_TYPES[geom.geom_type.num]
            g = OGRGeometry(multi_type)
            g.add(geom)
        else:
            g = geom

        # Transforming the geometry with our Coordinate Transformation object,
        # but only if the class variable `transform` is set w/a CoordTransform
        # object.
        if self.transform:
            g.transform(self.transform)

        # Returning the WKT of the geometry.
        return g.wkt