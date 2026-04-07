def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(archived=False)