def test13_attr_value(self):
        "Testing the attr_value() method."
        s1 = SpatialReference("WGS84")
        with self.assertRaises(TypeError):
            s1.__getitem__(0)
        with self.assertRaises(TypeError):
            s1.__getitem__(("GEOGCS", "foo"))
        self.assertEqual("WGS 84", s1["GEOGCS"])
        self.assertEqual("WGS_1984", s1["DATUM"])
        self.assertEqual("EPSG", s1["AUTHORITY"])
        self.assertEqual(4326, int(s1["AUTHORITY", 1]))
        self.assertIsNone(s1["FOOBAR"])