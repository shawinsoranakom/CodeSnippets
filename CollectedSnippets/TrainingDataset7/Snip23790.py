def test_post_data(self):
        res = self.client.post("/contact/", {"name": "Me", "message": "Hello"})
        self.assertRedirects(res, "/list/authors/")