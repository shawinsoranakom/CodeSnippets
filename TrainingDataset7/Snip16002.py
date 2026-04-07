def get_queryset(self, request):
        # Order by a field that isn't in list display, to be able to test
        # whether ordering is preserved.
        return super().get_queryset(request).order_by("age")