def test_include_3_tuple_namespace(self):
        msg = (
            "Cannot override the namespace for a dynamic module that provides a "
            "namespace."
        )
        with self.assertRaisesMessage(ImproperlyConfigured, msg):
            include((self.url_patterns, "app_name", "namespace"), "namespace")