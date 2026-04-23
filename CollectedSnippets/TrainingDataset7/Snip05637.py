def get_facet_counts(self, pk_attname, filtered_qs):
        return {
            f"{i}__c": models.Count(
                pk_attname,
                filter=models.Q(
                    (self.lookup_kwarg, value)
                    if value is not None
                    else (self.lookup_kwarg_isnull, True)
                ),
            )
            for i, value in enumerate(self.lookup_choices)
        }