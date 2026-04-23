def test_include_4_tuple(self):
        msg = "Passing a 4-tuple to include() is not supported."
        with self.assertRaisesMessage(ImproperlyConfigured, msg):
            include((self.url_patterns, "app_name", "namespace", "blah"))