def test_location_empty(self):
        msg = (
            "The storage backend of the staticfiles finder "
            "<class 'django.contrib.staticfiles.finders.DefaultStorageFinder'> "
            "doesn't have a valid location."
        )
        with self.assertRaisesMessage(ImproperlyConfigured, msg):
            finders.DefaultStorageFinder()