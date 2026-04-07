def test_follow_redirect(self):
        "A URL that redirects can be followed to termination."
        response = self.client.get("/double_redirect_view/", follow=True)
        self.assertRedirects(
            response, "/get_view/", status_code=302, target_status_code=200
        )
        self.assertEqual(len(response.redirect_chain), 2)