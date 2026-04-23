def get_facet_counts(self, pk_attname, filtered_qs):
        return {
            f"{i}__c": models.Count(pk_attname, filter=models.Q(**param_dict))
            for i, (_, param_dict) in enumerate(self.links)
        }