def test_float_integer_page(self):
        paginator = Paginator([1, 2, 3], 2)
        self.assertEqual(paginator.validate_number(1.0), 1)