def _response(self, template="foo", *args, **kwargs):
        template = engines["django"].from_string(template)
        return SimpleTemplateResponse(template, *args, **kwargs)