def test_bad_name(self):
        msg = (
            "WSGI application 'wsgi.wsgi.noexist' could not be loaded; Error importing"
        )
        with self.assertRaisesMessage(ImproperlyConfigured, msg):
            get_internal_wsgi_application()