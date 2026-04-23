def test_custom_renderer_error_dict(self):
        class CustomRenderer(DjangoTemplates):
            def render(self, template_name, context, request=None):
                if template_name == "django/forms/errors/dict/default.html":
                    return "<strong>So many errors!</strong>"
                return super().render(template_name, context, request)

        form = Form({}, renderer=CustomRenderer())
        form.full_clean()
        form.add_error(None, "Test error")

        self.assertHTMLEqual(
            form.errors.render(),
            "<strong>So many errors!</strong>",
        )