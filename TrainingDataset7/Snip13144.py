def render(self, context=None, request=None):
        if context is None:
            context = {}
        else:
            context = {k: conditional_escape(v) for k, v in context.items()}
        if request is not None:
            context["csrf_input"] = csrf_input_lazy(request)
            context["csrf_token"] = csrf_token_lazy(request)
        return self.safe_substitute(context)