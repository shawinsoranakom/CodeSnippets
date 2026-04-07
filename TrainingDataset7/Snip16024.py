def get_queryset(self, request):
        return super().get_queryset(request).defer("timestamp")