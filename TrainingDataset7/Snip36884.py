def test_no_template_source_loaders(self):
        """
        Make sure if you don't specify a template, the debug view doesn't blow
        up.
        """
        with self.assertLogs("django.request", "ERROR"):
            with self.assertRaises(TemplateDoesNotExist):
                self.client.get("/render_no_template/")