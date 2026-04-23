def _response(self, template="foo", *args, **kwargs):
        self._request = self.factory.get("/")
        template = engines["django"].from_string(template)
        return TemplateResponse(self._request, template, *args, **kwargs)