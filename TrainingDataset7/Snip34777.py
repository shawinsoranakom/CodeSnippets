def test_redirect_chain_delete(self):
        "A redirect chain will be followed from an initial DELETE request"
        response = self.client.delete("/redirects/", follow=True)
        self.assertRedirects(response, "/no_template_view/", 302, 200)
        self.assertEqual(len(response.redirect_chain), 3)