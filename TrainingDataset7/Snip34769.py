def test_redirect_chain_to_non_existent(self):
        "You can follow a chain to a nonexistent view."
        response = self.client.get("/redirect_to_non_existent_view2/", {}, follow=True)
        self.assertRedirects(
            response, "/non_existent_view/", status_code=302, target_status_code=404
        )