def process_rhs(self, qn, connection):
        if not isinstance(self.rhs, (SearchQuery, CombinedSearchQuery)):
            config = getattr(self.lhs, "config", None)
            self.rhs = SearchQuery(self.rhs, config=config)
        rhs, rhs_params = super().process_rhs(qn, connection)
        return rhs, rhs_params