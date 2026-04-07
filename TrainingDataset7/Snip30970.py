def test_pk_with_mixed_case_db_column(self):
        """
        A raw query with a model that has a pk db_column with mixed case.
        """
        query = "SELECT * FROM raw_query_mixedcaseidcolumn"
        queryset = MixedCaseIDColumn.objects.all()
        self.assertSuccessfulRawQuery(MixedCaseIDColumn, query, queryset)