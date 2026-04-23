def test_subquery_in_raw_sql(self):
        list(
            Book.objects.raw(
                "SELECT id FROM "
                "(SELECT * FROM raw_query_book WHERE paperback IS NOT NULL) sq"
            )
        )