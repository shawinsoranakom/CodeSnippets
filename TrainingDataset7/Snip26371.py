def test_joined_sql(self):
        # The underlying query only makes one join when a related table is
        # referenced twice.
        queryset = Article.objects.filter(
            reporter__first_name__exact="John", reporter__last_name__exact="Smith"
        )
        self.assertNumQueries(1, list, queryset)
        self.assertEqual(
            queryset.query.get_compiler(queryset.db).as_sql()[0].count("INNER JOIN"), 1
        )