def process_view(self, request, view_func, view_args, view_kwargs):
        template = engines["django"].from_string(
            "Processed view {{ view }}{% for m in mw %}\n{{ m }}{% endfor %}"
        )
        return TemplateResponse(
            request,
            template,
            {"mw": [self.__class__.__name__], "view": view_func.__name__},
        )