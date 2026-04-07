def test_get_post_view(self):
        "GET a view that normally expects POSTs"
        response = self.client.get("/post_view/", {})

        # Check some response details
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.templates[0].name, "Empty GET Template")
        self.assertTemplateUsed(response, "Empty GET Template")
        self.assertTemplateNotUsed(response, "Empty POST Template")