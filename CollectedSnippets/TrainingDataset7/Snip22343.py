def test_view_flatpage(self):
        "A flatpage can be served through a view"
        response = self.client.get("/flatpage_root/flatpage/")
        self.assertContains(response, "<p>Isn't it flat!</p>")