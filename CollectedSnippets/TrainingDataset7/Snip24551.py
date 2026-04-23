def test_lookup_input_tuple_too_long(self):
        rast = GDALRaster(json.loads(JSON_RASTER))
        msg = "Tuple too long for lookup bbcontains."
        with self.assertRaisesMessage(ValueError, msg):
            RasterModel.objects.filter(rast__bbcontains=(rast, 1, 2))