def queryset(self, request, queryset):
        decade = self.value()
        if decade == "the 80s":
            return queryset.filter(year__gte=1980, year__lte=1989)
        if decade == "the 90s":
            return queryset.filter(year__gte=1990, year__lte=1999)
        if decade == "the 00s":
            return queryset.filter(year__gte=2000, year__lte=2009)