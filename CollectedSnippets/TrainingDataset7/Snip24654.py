def test_init_invalid(self):
        "Testing initialization from invalid units"
        with self.assertRaises(AttributeError):
            D(banana=100)