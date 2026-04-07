def test_default(self):
        """
        If ``WSGI_APPLICATION`` is ``None``, the return value of
        ``get_wsgi_application`` is returned.
        """
        # Mock out get_wsgi_application so we know its return value is used
        fake_app = object()

        def mock_get_wsgi_app():
            return fake_app

        from django.core.servers import basehttp

        _orig_get_wsgi_app = basehttp.get_wsgi_application
        basehttp.get_wsgi_application = mock_get_wsgi_app

        try:
            app = get_internal_wsgi_application()

            self.assertIs(app, fake_app)
        finally:
            basehttp.get_wsgi_application = _orig_get_wsgi_app