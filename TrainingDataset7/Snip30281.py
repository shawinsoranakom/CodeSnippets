def get_queryset(self):
        return super().get_queryset().exclude(name="fred")