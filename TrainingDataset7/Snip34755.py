def test_assert_not_contains_renders_template_response(self):
        """
        An unrendered SimpleTemplateResponse may be used in
        assertNotContains().
        """
        template = engines["django"].from_string("Hello")
        response = SimpleTemplateResponse(template)
        self.assertNotContains(response, "Bye")