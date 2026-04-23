def get_queryset(self, request):
        return super().get_queryset(request).filter(pk__gt=1)