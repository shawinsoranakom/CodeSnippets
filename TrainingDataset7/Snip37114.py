def test_bad_module(self):
        msg = "WSGI application 'wsgi.noexist.app' could not be loaded; Error importing"
        with self.assertRaisesMessage(ImproperlyConfigured, msg):
            get_internal_wsgi_application()