def get_queryset(self):
        return super().get_queryset().filter(top_speed__gt=150)