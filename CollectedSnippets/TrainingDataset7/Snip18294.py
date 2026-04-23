def test_get_default_redirect_url_no_next_page(self):
        msg = "No URL to redirect to. Provide a next_page."
        with self.assertRaisesMessage(ImproperlyConfigured, msg):
            RedirectURLMixin().get_default_redirect_url()