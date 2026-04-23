def test_annotate_joins(self):
        """
        The base table's join isn't promoted to LOUTER. This could
        cause the query generation to fail if there is an exclude() for
        fk-field in the query, too. Refs #19087.
        """
        qs = Book.objects.annotate(n=Count("pk"))
        self.assertIs(qs.query.alias_map["aggregation_regress_book"].join_type, None)
        # The query executes without problems.
        self.assertEqual(len(qs.exclude(publisher=-1)), 6)