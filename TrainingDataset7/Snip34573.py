def test_post(self):
        "POST some data to a view"
        post_data = {"value": 37}
        response = self.client.post("/post_view/", post_data)

        # Check some response details
        self.assertContains(response, "Data received")
        self.assertEqual(response.context["data"], "37")
        self.assertEqual(response.templates[0].name, "POST Template")