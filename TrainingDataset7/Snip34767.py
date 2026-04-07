def test_redirect_chain(self):
        "You can follow a redirect chain of multiple redirects"
        response = self.client.get("/redirects/further/more/", {}, follow=True)
        self.assertRedirects(
            response, "/no_template_view/", status_code=302, target_status_code=200
        )

        self.assertEqual(len(response.redirect_chain), 1)
        self.assertEqual(response.redirect_chain[0], ("/no_template_view/", 302))