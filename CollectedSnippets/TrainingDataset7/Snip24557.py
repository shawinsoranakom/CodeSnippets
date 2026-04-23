def test_lookup_with_raster_bbox(self):
        rast = GDALRaster(json.loads(JSON_RASTER))
        # Shift raster upward
        rast.origin.y = 2
        # The raster in the model is not strictly below
        qs = RasterModel.objects.filter(rast__strictly_below=rast)
        self.assertEqual(qs.count(), 0)
        # Shift raster further upward
        rast.origin.y = 6
        # The raster in the model is strictly below
        qs = RasterModel.objects.filter(rast__strictly_below=rast)
        self.assertEqual(qs.count(), 1)