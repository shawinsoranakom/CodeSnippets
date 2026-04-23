def test_get_default_redirect_url_next_page(self):
        class RedirectURLView(RedirectURLMixin):
            next_page = "/custom/"

        self.assertEqual(RedirectURLView().get_default_redirect_url(), "/custom/")