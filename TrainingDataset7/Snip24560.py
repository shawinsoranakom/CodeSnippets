def test_db_function_errors(self):
        """
        Errors are raised when using DB functions with raster content.
        """
        point = GEOSGeometry("SRID=3086;POINT (-697024.9213808845 683729.1705516104)")
        rast = GDALRaster(json.loads(JSON_RASTER))
        msg = "Distance function requires a geometric argument in position 2."
        with self.assertRaisesMessage(TypeError, msg):
            RasterModel.objects.annotate(distance_from_point=Distance("geom", rast))
        with self.assertRaisesMessage(TypeError, msg):
            RasterModel.objects.annotate(
                distance_from_point=Distance("rastprojected", rast)
            )
        msg = (
            "Distance function requires a GeometryField in position 1, got RasterField."
        )
        with self.assertRaisesMessage(TypeError, msg):
            RasterModel.objects.annotate(
                distance_from_point=Distance("rastprojected", point)
            ).count()