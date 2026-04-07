def test_include_namespace(self):
        msg = (
            "Specifying a namespace in include() without providing an "
            "app_name is not supported."
        )
        with self.assertRaisesMessage(ImproperlyConfigured, msg):
            include(self.url_patterns, "namespace")