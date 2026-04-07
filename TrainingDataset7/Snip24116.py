def test_band_delete_nodata(self):
        rsmem = GDALRaster(
            {
                "srid": 4326,
                "width": 1,
                "height": 1,
                "bands": [{"data": [0], "nodata_value": 1}],
            }
        )
        rsmem.bands[0].nodata_value = None
        self.assertIsNone(rsmem.bands[0].nodata_value)