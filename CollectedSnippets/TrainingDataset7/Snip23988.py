def test02_invalid_driver(self):
        "Testing invalid GDAL/OGR Data Source Drivers."
        for i in invalid_drivers:
            with self.assertRaises(GDALException):
                Driver(i)