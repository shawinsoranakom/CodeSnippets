def test_extra_template_params(self):
        """
        A template view can be customized to return extra context.
        """
        response = self.client.get("/template/custom/bar/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["foo"], "bar")
        self.assertEqual(response.context["key"], "value")
        self.assertIsInstance(response.context["view"], View)