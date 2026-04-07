def get_sortable_by(self, request):
        """Hook for specifying which fields can be sorted in the changelist."""
        return (
            self.sortable_by
            if self.sortable_by is not None
            else self.get_list_display(request)
        )