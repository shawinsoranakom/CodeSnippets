def test_lookup_input_band_not_allowed(self):
        rast = GDALRaster(json.loads(JSON_RASTER))
        qs = RasterModel.objects.filter(rast__bbcontains=(rast, 1))
        msg = "Band indices are not allowed for this operator, it works on bbox only."
        with self.assertRaisesMessage(ValueError, msg):
            qs.count()