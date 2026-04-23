def test_get_finder_bad_classname(self):
        with self.assertRaises(ImportError):
            finders.get_finder("django.contrib.staticfiles.finders.FooBarFinder")