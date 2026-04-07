def test_invalid_default_bounds(self):
        tests = [")]", ")[", "](", "])", "([", "[(", "x", "", None]
        msg = "default_bounds must be one of '[)', '(]', '()', or '[]'."
        for invalid_bounds in tests:
            with self.assertRaisesMessage(ValueError, msg):
                pg_fields.DecimalRangeField(default_bounds=invalid_bounds)