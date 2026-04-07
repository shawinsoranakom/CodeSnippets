def test_view_flatpage(self):
        """
        A flatpage can be served through a view, even when the middleware is in
        use
        """
        response = self.client.get("/flatpage_root/flatpage/")
        self.assertContains(response, "<p>Isn't it flat!</p>")