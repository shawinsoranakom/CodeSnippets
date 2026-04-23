def get_queryset(self):
        return super().get_queryset().filter(pk__gt=1)