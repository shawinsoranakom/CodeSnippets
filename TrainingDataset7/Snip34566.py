def test_get_view(self):
        "GET a view"
        # The data is ignored, but let's check it doesn't crash the system
        # anyway.
        data = {"var": "\xf2"}
        response = self.client.get("/get_view/", data)

        # Check some response details
        self.assertContains(response, "This is a test")
        self.assertEqual(response.context["var"], "\xf2")
        self.assertEqual(response.templates[0].name, "GET Template")