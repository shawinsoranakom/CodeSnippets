def test_band_statistics_empty_band(self):
        rsmem = GDALRaster(
            {
                "srid": 4326,
                "width": 1,
                "height": 1,
                "bands": [{"data": [0], "nodata_value": 0}],
            }
        )
        self.assertEqual(rsmem.bands[0].statistics(), (None, None, None, None))