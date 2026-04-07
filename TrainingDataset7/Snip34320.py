def test_filter_name_arg(self):
        @self.library.filter("name")
        def func():
            return ""

        self.assertEqual(self.library.filters["name"], func)