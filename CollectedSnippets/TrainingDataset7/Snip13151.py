def render(self, context=None, request=None):
        if context is None:
            context = {}
        if request is not None:
            context["request"] = request
            context["csrf_input"] = csrf_input_lazy(request)
            context["csrf_token"] = csrf_token_lazy(request)
            for context_processor in self.backend.template_context_processors:
                context.update(context_processor(request))
        try:
            return self.template.render(context)
        except jinja2.TemplateSyntaxError as exc:
            new = TemplateSyntaxError(exc.args)
            new.template_debug = get_exception_info(exc)
            raise new from exc