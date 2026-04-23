def test_reverse_lazy_decodes(self):
        "reverse_lazy() works in the test client"
        data = {"var": "data"}
        response = self.client.get(reverse_lazy("get_view"), data)

        # Check some response details
        self.assertContains(response, "This is a test")