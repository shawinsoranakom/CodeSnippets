def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(department__id=self.value())