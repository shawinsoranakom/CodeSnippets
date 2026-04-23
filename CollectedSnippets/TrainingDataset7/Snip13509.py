def content(self, value):
        """Set the content for the response."""
        HttpResponse.content.fset(self, value)
        self._is_rendered = True