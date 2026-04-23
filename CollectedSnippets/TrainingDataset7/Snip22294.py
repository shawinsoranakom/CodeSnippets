def test_fallback_flatpage(self):
        "A flatpage can be served by the fallback middleware"
        response = self.client.get("/flatpage/")
        self.assertContains(response, "<p>Isn't it flat!</p>")