def get_facet_counts(self, pk_attname, filtered_qs):
        return {
            "true__c": models.Count(
                pk_attname, filter=models.Q(**{self.field_path: True})
            ),
            "false__c": models.Count(
                pk_attname, filter=models.Q(**{self.field_path: False})
            ),
            "null__c": models.Count(
                pk_attname, filter=models.Q(**{self.lookup_kwarg2: True})
            ),
        }