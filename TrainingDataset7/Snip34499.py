def test_custom_urlconf(self):
        response = self.client.get("/template_response_view/")
        self.assertContains(response, "This is where you can find the snark: /snark/")