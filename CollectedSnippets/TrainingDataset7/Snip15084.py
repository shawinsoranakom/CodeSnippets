def get_queryset(self, request):
        return super().get_queryset(request).select_related("parent")