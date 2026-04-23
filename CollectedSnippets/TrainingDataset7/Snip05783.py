def add_view(self, request, form_url="", extra_context=None):
        return self.changeform_view(request, None, form_url, extra_context)