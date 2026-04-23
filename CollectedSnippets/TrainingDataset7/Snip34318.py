def test_filter(self):
        @self.library.filter
        def func():
            return ""

        self.assertEqual(self.library.filters["func"], func)