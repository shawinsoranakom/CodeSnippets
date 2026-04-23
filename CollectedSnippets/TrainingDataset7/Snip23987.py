def test01_valid_driver(self):
        "Testing valid GDAL/OGR Data Source Drivers."
        for d in valid_drivers:
            dr = Driver(d)
            self.assertEqual(d, str(dr))