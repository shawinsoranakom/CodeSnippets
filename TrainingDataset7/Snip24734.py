def test_middleware_returns_none(self):
        msg = "Middleware factory handlers.tests.empty_middleware returned None."
        with self.assertRaisesMessage(ImproperlyConfigured, msg):
            self.client.get("/")