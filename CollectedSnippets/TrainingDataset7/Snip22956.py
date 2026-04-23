def render(self, template_name, context, request=None):
                if template_name == "django/forms/errors/dict/default.html":
                    return "<strong>So many errors!</strong>"
                return super().render(template_name, context, request)