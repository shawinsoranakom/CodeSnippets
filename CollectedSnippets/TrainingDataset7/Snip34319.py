def test_filter_parens(self):
        @self.library.filter()
        def func():
            return ""

        self.assertEqual(self.library.filters["func"], func)