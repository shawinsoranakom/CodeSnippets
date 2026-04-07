def test_nested_requests(self):
        """
        response.context is not lost when view call another view.
        """
        response = self.client.get("/nested_view/")
        self.assertIsInstance(response.context, RequestContext)
        self.assertEqual(response.context["nested"], "yes")