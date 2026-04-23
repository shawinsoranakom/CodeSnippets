def test_assert_not_contains_using_non_template_response(self):
        """
        auto-rendering does not affect responses that aren't instances (or
        subclasses) of SimpleTemplateResponse.
        """
        response = HttpResponse("Hello")
        self.assertNotContains(response, "Bye")