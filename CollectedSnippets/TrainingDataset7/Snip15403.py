def queryset(self, request, queryset):
        queryset = queryset.annotate(
            owned_book_count=models.Count(
                "employee__department",
                filter=models.Q(employee__department__code="DEV"),
            ),
        )

        if self.value() == "DEV_OWNED":
            return queryset.filter(owned_book_count__gt=0)
        elif self.value() == "OTHER":
            return queryset.filter(owned_book_count=0)