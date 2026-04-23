def test_init_invalid_area_only_units(self):
        with self.assertRaises(AttributeError):
            D(ha=100)