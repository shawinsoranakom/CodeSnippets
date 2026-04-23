def test_init_invalid_a(self):
        "Testing initialization from invalid units"
        with self.assertRaises(AttributeError):
            A(banana=100)