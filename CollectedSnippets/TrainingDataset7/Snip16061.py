def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(is_superuser=False)