def get_queryset(self):
        return super().get_queryset().filter(cover_blown=False)