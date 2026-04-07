def test_gdalraster_input_as_path(self):
        rs_path = Path(__file__).parent.parent / "data" / "rasters" / "raster.tif"
        rs = GDALRaster(rs_path)
        self.assertEqual(str(rs_path), rs.name)