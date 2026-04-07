def get_facet_counts(self, pk_attname, filtered_qs):
        lookup_condition = self.get_lookup_condition()
        return {
            "empty__c": models.Count(pk_attname, filter=lookup_condition),
            "not_empty__c": models.Count(pk_attname, filter=~lookup_condition),
        }