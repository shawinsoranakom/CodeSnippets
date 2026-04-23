def get_queryset(self):
        return super().get_queryset().filter(authors__name__icontains="sir")