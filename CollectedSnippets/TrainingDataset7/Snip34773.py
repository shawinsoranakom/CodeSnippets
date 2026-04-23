def test_redirect_chain_post(self):
        "A redirect chain will be followed from an initial POST post"
        response = self.client.post("/redirects/", {"nothing": "to_send"}, follow=True)
        self.assertRedirects(response, "/no_template_view/", 302, 200)
        self.assertEqual(len(response.redirect_chain), 3)