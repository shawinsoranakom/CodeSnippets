def render(self, context=None, request=None):
        context = make_context(
            context, request, autoescape=self.backend.engine.autoescape
        )
        try:
            return self.template.render(context)
        except TemplateDoesNotExist as exc:
            reraise(exc, self.backend)