def get_queryset(self):
        return super().get_queryset().prefetch_related("permissions")