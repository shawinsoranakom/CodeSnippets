def setUp(self):
        self.rs_path = os.path.join(
            os.path.dirname(__file__), "../data/rasters/raster.tif"
        )
        self.rs = GDALRaster(self.rs_path)