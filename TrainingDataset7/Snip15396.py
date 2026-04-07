def lookups(self, request, model_admin):
        qs = model_admin.get_queryset(request)
        if qs.filter(year__gte=1980, year__lte=1989).exists():
            yield ("the 80s", "the 1980's")
        if qs.filter(year__gte=1990, year__lte=1999).exists():
            yield ("the 90s", "the 1990's")
        if qs.filter(year__gte=2000, year__lte=2009).exists():
            yield ("the 00s", "the 2000's")