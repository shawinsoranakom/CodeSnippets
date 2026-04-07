def get_search_fields(self, request):
        """
        Return a sequence containing the fields to be searched whenever
        somebody submits a search query.
        """
        return self.search_fields