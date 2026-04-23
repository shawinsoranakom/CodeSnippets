def queryset(self, request, queryset):
        """
        Return the filtered queryset.
        """
        raise NotImplementedError(
            "subclasses of ListFilter must provide a queryset() method"
        )