def test_urlconf_is_reset_after_request(self):
        """The URLconf is reset after each request."""
        self.assertIsNone(get_urlconf())
        with override_settings(
            MIDDLEWARE=["%s.ChangeURLconfMiddleware" % middleware.__name__]
        ):
            self.client.get(reverse("inner"))
        self.assertIsNone(get_urlconf())