def test_include_3_tuple(self):
        msg = "Passing a 3-tuple to include() is not supported."
        with self.assertRaisesMessage(ImproperlyConfigured, msg):
            include((self.url_patterns, "app_name", "namespace"))