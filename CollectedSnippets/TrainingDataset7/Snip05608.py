def get_facet_counts(self, pk_attname, filtered_qs):
        original_value = self.used_parameters.get(self.parameter_name)
        counts = {}
        for i, choice in enumerate(self.lookup_choices):
            self.used_parameters[self.parameter_name] = choice[0]
            lookup_qs = self.queryset(self.request, filtered_qs)
            if lookup_qs is not None:
                counts[f"{i}__c"] = models.Count(
                    pk_attname,
                    filter=models.Q(pk__in=lookup_qs),
                )
        self.used_parameters[self.parameter_name] = original_value
        return counts