def get_queryset(self):
        return super().get_queryset().filter(value=42)