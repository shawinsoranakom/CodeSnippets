def queryset(self, request, queryset):
        if self.lookup_kwarg not in self.used_parameters:
            return queryset
        if self.lookup_val not in ("0", "1"):
            raise IncorrectLookupParameters

        lookup_condition = self.get_lookup_condition()
        if self.lookup_val == "1":
            return queryset.filter(lookup_condition)
        return queryset.exclude(lookup_condition)