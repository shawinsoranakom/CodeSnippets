def test_query_count(self):
        self.assertNumQueries(
            1, list, Author.objects.raw("SELECT * FROM raw_query_author")
        )