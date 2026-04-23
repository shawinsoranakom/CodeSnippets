def test_filter_call(self):
        def func():
            return ""

        self.library.filter("name", func)
        self.assertEqual(self.library.filters["name"], func)