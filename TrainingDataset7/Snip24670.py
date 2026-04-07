def test_access_invalid_a(self):
        "Testing access in invalid units"
        a = A(sq_m=100)
        self.assertFalse(hasattr(a, "banana"))