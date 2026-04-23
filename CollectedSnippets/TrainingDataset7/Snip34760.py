def test_template_rendered_multiple_times(self):
        """
        Template assertions work when a template is rendered multiple times.
        """
        response = self.client.get("/render_template_multiple_times/")

        self.assertTemplateUsed(response, "base.html", count=2)