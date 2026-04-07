def test_redirect_chain_put(self):
        "A redirect chain will be followed from an initial PUT request"
        response = self.client.put("/redirects/", follow=True)
        self.assertRedirects(response, "/no_template_view/", 302, 200)
        self.assertEqual(len(response.redirect_chain), 3)