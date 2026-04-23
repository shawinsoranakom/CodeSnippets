def add_view(self, request, *args, **kwargs):
        request.is_add_view = True
        return super().add_view(request, *args, **kwargs)