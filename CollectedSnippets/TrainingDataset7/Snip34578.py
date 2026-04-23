def test_trace(self):
        """TRACE a view"""
        response = self.client.trace("/trace_view/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["method"], "TRACE")
        self.assertEqual(response.templates[0].name, "TRACE Template")