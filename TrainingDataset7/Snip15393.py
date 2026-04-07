def queryset(self, request, queryset):
        if self.value() == "the 90s":
            return queryset.filter(year__gte=1990, year__lte=1999)
        else:
            return queryset.exclude(year__gte=1990, year__lte=1999)