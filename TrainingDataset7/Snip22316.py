def test_redirect_view_flatpage(self):
        "A flatpage can be served through a view and should add a slash"
        response = self.client.get("/flatpage_root/flatpage")
        self.assertRedirects(response, "/flatpage_root/flatpage/", status_code=301)