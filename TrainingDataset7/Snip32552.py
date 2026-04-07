def test_media_url_in_static_url(self):
        msg = "runserver can't serve media if MEDIA_URL is within STATIC_URL."
        with self.assertRaisesMessage(ImproperlyConfigured, msg):
            check_settings()
        with self.settings(DEBUG=False):  # Check disabled if DEBUG=False.
            check_settings()