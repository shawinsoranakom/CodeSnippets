def test_extra_context(self):
        response = self.client.get("/template/extra_context/")
        self.assertEqual(response.context["title"], "Title")