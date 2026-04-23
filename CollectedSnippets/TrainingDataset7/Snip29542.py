def test_search_vector_field(self):
        class SearchModel(PostgreSQLModel):
            search_vector = SearchVectorField()
            search_query = SearchQueryField()

        vector_field = SearchModel._meta.get_field("search_vector")
        query_field = SearchModel._meta.get_field("search_query")
        self.assert_model_check_errors(
            SearchModel,
            [
                self._make_error(vector_field, "SearchVectorField"),
                self._make_error(query_field, "SearchQueryField"),
            ],
        )