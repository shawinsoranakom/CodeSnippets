def test_filter_name_kwarg(self):
        @self.library.filter(name="name")
        def func():
            return ""

        self.assertEqual(self.library.filters["name"], func)