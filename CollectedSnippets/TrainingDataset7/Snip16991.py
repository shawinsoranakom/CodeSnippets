def test_aggregation_filter_exists(self):
        publishers_having_more_than_one_book_qs = (
            Book.objects.values("publisher")
            .annotate(cnt=Count("isbn"))
            .filter(cnt__gt=1)
        )
        query = publishers_having_more_than_one_book_qs.query.exists()
        _, _, group_by = query.get_compiler(connection=connection).pre_sql_setup()
        self.assertEqual(len(group_by), 1)