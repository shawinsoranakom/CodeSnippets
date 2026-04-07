def get_facet_queryset(self, changelist):
        filtered_qs = changelist.get_queryset(
            self.request, exclude_parameters=self.expected_parameters()
        )
        return filtered_qs.aggregate(
            **self.get_facet_counts(changelist.pk_attname, filtered_qs)
        )