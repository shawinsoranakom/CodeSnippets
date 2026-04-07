def get_queryset(self):
        return super().get_queryset().select_related("details")