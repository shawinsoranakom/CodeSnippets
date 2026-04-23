def test_success(self):
        """
        If ``WSGI_APPLICATION`` is a dotted path, the referenced object is
        returned.
        """
        app = get_internal_wsgi_application()

        from .wsgi import application

        self.assertIs(app, application)