def test_custom_template_does_not_exist(self):
        """An exception is raised if a nonexistent template is supplied."""
        factory = RequestFactory()
        request = factory.post("/")
        with self.assertRaises(TemplateDoesNotExist):
            csrf_failure(request, template_name="nonexistent.html")