def get_facet_counts(self, pk_attname, filtered_qs):
        counts = {
            f"{pk_val}__c": models.Count(
                pk_attname, filter=models.Q(**{self.lookup_kwarg: pk_val})
            )
            for pk_val, _ in self.lookup_choices
        }
        if self.include_empty_choice:
            counts["__c"] = models.Count(
                pk_attname, filter=models.Q(**{self.lookup_kwarg_isnull: True})
            )
        return counts