def test_urlize_http_default_warning(self):
        msg = (
            "The default protocol will be changed from HTTP to HTTPS in Django 7.0. "
            "Set the URLIZE_ASSUME_HTTPS transitional setting to True to opt into "
            "using HTTPS as the new default protocol."
        )
        with self.assertWarnsMessage(RemovedInDjango70Warning, msg):
            self.assertEqual(
                urlize("Visit example.com"),
                'Visit <a href="http://example.com">example.com</a>',
            )