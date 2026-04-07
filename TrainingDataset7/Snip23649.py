def test_template_params(self):
        """
        A generic template view passes kwargs as context.
        """
        response = self.client.get("/template/simple/bar/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["foo"], "bar")
        self.assertIsInstance(response.context["view"], View)