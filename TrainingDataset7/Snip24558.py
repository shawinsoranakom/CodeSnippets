def test_lookup_with_polygonized_raster(self):
        rast = GDALRaster(json.loads(JSON_RASTER))
        # Move raster to overlap with the model point on the left side
        rast.origin.x = -95.37040 + 1
        rast.origin.y = 29.70486
        # Raster overlaps with point in model
        qs = RasterModel.objects.filter(geom__intersects=rast)
        self.assertEqual(qs.count(), 1)
        # Change left side of raster to be nodata values
        rast.bands[0].data(data=[0, 0, 0, 1, 1], shape=(5, 1))
        rast.bands[0].nodata_value = 0
        qs = RasterModel.objects.filter(geom__intersects=rast)
        # Raster does not overlap anymore after polygonization
        # where the nodata zone is not included.
        self.assertEqual(qs.count(), 0)