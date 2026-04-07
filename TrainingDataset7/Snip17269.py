def _perform_query(self):
        from ..models import TotallyNormal

        queryset = TotallyNormal.objects.using(self.database)
        queryset.update_or_create(name="new name")
        self.query_results = list(queryset.values_list("name"))