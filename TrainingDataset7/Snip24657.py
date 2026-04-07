def test_access_invalid(self):
        "Testing access in invalid units"
        d = D(m=100)
        self.assertFalse(hasattr(d, "banana"))