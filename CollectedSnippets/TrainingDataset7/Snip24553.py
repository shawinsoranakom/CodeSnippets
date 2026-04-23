def test_lookup_invalid_band_rhs(self):
        rast = GDALRaster(json.loads(JSON_RASTER))
        qs = RasterModel.objects.filter(rast__contains=(rast, "evil"))
        msg = "Band index must be an integer, but got 'str'."
        with self.assertRaisesMessage(TypeError, msg):
            qs.count()