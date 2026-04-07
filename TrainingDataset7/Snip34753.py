def test_assert_contains_renders_template_response(self):
        """
        An unrendered SimpleTemplateResponse may be used in assertContains().
        """
        template = engines["django"].from_string("Hello")
        response = SimpleTemplateResponse(template)
        self.assertContains(response, "Hello")