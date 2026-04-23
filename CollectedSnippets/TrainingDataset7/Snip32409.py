def test_get_finder_bad_module(self):
        with self.assertRaises(ImportError):
            finders.get_finder("foo.bar.FooBarFinder")