def test_custom_templates_wrong(self):
        """
        Default error views should raise TemplateDoesNotExist when passed a
        template that doesn't exist.
        """
        request = self.request_factory.get("/")

        with self.assertRaises(TemplateDoesNotExist):
            bad_request(request, Exception(), template_name="nonexistent")

        with self.assertRaises(TemplateDoesNotExist):
            permission_denied(request, Exception(), template_name="nonexistent")

        with self.assertRaises(TemplateDoesNotExist):
            page_not_found(request, Http404(), template_name="nonexistent")

        with self.assertRaises(TemplateDoesNotExist):
            server_error(request, template_name="nonexistent")