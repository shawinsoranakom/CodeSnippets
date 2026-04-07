def test_url_parameters(self):
        "Make sure that URL ;-parameters are not stripped."
        response = self.client.get("/unknown_view/;some-parameter")

        # The path in the response includes it (ignore that it's a 404)
        self.assertEqual(response.request["PATH_INFO"], "/unknown_view/;some-parameter")