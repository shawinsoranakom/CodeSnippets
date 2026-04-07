def test_redirect_chain_options(self):
        "A redirect chain will be followed from an initial OPTIONS request"
        response = self.client.options("/redirects/", follow=True)
        self.assertRedirects(response, "/no_template_view/", 302, 200)
        self.assertEqual(len(response.redirect_chain), 3)