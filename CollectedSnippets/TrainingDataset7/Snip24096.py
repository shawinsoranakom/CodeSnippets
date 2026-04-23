def test_vsi_vsizip_filesystem(self):
        rst_zipfile = NamedTemporaryFile(suffix=".zip")
        with zipfile.ZipFile(rst_zipfile, mode="w") as zf:
            zf.write(self.rs_path, "raster.tif")
        rst_path = "/vsizip/" + os.path.join(rst_zipfile.name, "raster.tif")
        rst = GDALRaster(rst_path)
        self.assertEqual(rst.driver.name, self.rs.driver.name)
        self.assertEqual(rst.name, rst_path)
        self.assertIs(rst.is_vsi_based, True)
        self.assertIsNone(rst.vsi_buffer)