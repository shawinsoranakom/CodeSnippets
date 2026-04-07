def test02_invalid_shp(self):
        "Testing invalid SHP files for the Data Source."
        for source in bad_ds:
            with self.assertRaises(GDALException):
                DataSource(source.ds)