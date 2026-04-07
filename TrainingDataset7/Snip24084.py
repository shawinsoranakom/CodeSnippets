def test_rs_srid(self):
        rast = GDALRaster(
            {
                "width": 16,
                "height": 16,
                "srid": 4326,
            }
        )
        self.assertEqual(rast.srid, 4326)
        rast.srid = 3086
        self.assertEqual(rast.srid, 3086)