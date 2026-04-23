def test_assert_contains_using_non_template_response(self):
        """auto-rendering does not affect responses that aren't
        instances (or subclasses) of SimpleTemplateResponse.
        Refs #15826.
        """
        response = HttpResponse("Hello")
        self.assertContains(response, "Hello")