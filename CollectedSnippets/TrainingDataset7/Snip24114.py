def test_band_statistics_automatic_refresh(self):
        rsmem = GDALRaster(
            {
                "srid": 4326,
                "width": 2,
                "height": 2,
                "bands": [{"data": [0] * 4, "nodata_value": 99}],
            }
        )
        band = rsmem.bands[0]
        # Populate statistics cache
        self.assertEqual(band.statistics(), (0, 0, 0, 0))
        # Change data
        band.data([1, 1, 0, 0])
        # Statistics are properly updated
        self.assertEqual(band.statistics(), (0.0, 1.0, 0.5, 0.5))
        # Change nodata_value
        band.nodata_value = 0
        # Statistics are properly updated
        self.assertEqual(band.statistics(), (1.0, 1.0, 1.0, 0.0))