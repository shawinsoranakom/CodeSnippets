def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(public=True, tag__name="t1")