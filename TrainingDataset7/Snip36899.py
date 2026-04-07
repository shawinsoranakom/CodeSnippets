def test_template_not_found_error(self):
        # Raises a TemplateDoesNotExist exception and shows the debug view.
        url = reverse(
            "raises_template_does_not_exist", kwargs={"path": "notfound.html"}
        )
        with self.assertLogs("django.request", "ERROR"):
            response = self.client.get(url)
        self.assertContains(response, '<div class="context" id="', status_code=500)