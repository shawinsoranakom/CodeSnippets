def test_empty_post(self):
        "POST an empty dictionary to a view"
        response = self.client.post("/post_view/", {})

        # Check some response details
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.templates[0].name, "Empty POST Template")
        self.assertTemplateNotUsed(response, "Empty GET Template")
        self.assertTemplateUsed(response, "Empty POST Template")