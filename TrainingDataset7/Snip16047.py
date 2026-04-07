def change_view(self, request, *args, **kwargs):
        request.is_add_view = False
        return super().change_view(request, *args, **kwargs)