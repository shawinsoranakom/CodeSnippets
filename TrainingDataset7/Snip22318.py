def test_redirect_fallback_flatpage(self):
        """
        A flatpage can be served by the fallback middleware and should add a
        slash
        """
        response = self.client.get("/flatpage")
        self.assertRedirects(response, "/flatpage/", status_code=301)