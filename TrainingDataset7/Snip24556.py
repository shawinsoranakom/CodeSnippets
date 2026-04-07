def test_result_of_gis_lookup_with_rasters(self):
        # Point is in the interior
        qs = RasterModel.objects.filter(
            rast__contains=GEOSGeometry("POINT (-0.5 0.5)", 4326)
        )
        self.assertEqual(qs.count(), 1)
        # Point is in the exterior
        qs = RasterModel.objects.filter(
            rast__contains=GEOSGeometry("POINT (0.5 0.5)", 4326)
        )
        self.assertEqual(qs.count(), 0)
        # A point on the boundary is not contained properly
        qs = RasterModel.objects.filter(
            rast__contains_properly=GEOSGeometry("POINT (0 0)", 4326)
        )
        self.assertEqual(qs.count(), 0)
        # Raster is located left of the point
        qs = RasterModel.objects.filter(rast__left=GEOSGeometry("POINT (1 0)", 4326))
        self.assertEqual(qs.count(), 1)