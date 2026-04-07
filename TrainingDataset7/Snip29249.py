def get_queryset(self):
        return super().get_queryset().filter(is_temp=False)