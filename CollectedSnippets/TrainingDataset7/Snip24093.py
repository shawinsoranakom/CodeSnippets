def test_vsi_raster_deletion(self):
        path = "/vsimem/raster.tif"
        # Create a vsi-based raster from scratch.
        vsimem = GDALRaster(
            {
                "name": path,
                "driver": "tif",
                "width": 4,
                "height": 4,
                "srid": 4326,
                "bands": [
                    {
                        "data": range(16),
                    }
                ],
            }
        )
        # The virtual file exists.
        rst = GDALRaster(path)
        self.assertEqual(rst.width, 4)
        # Delete GDALRaster.
        del vsimem
        del rst
        # The virtual file has been removed.
        msg = 'Could not open the datasource at "/vsimem/raster.tif"'
        with self.assertRaisesMessage(GDALException, msg):
            GDALRaster(path)