def queryset(self, request, queryset):
        if self.value() == "yes":
            return queryset.filter(is_active=True)
        else:
            return queryset.filter(is_active=False)