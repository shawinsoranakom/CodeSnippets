def _build_search_args(self):
        # Clean up the search query
        query = self.search_query if isinstance(self.search_query, str) and self.search_query.strip() else None
        lexical_terms = self.lexical_terms or None

        # Check if we have a search query, and if so set the args
        if query:
            args = {
                "query": query,
                "search_type": self._map_search_type(),
                "k": self.number_of_results,
                "score_threshold": self.search_score_threshold,
                "lexical_query": lexical_terms,
            }
        elif self.advanced_search_filter:
            args = {
                "n": self.number_of_results,
            }
        else:
            return {}

        filter_arg = self.advanced_search_filter or {}
        if filter_arg:
            args["filter"] = filter_arg

        return args