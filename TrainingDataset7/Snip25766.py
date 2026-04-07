def test_in_bulk_lots_of_ids(self):
        test_range = 2000
        max_query_params = connection.features.max_query_params
        expected_num_queries = (
            ceil(test_range / max_query_params) if max_query_params else 1
        )
        Author.objects.bulk_create(
            [Author() for i in range(test_range - Author.objects.count())]
        )
        authors = {author.pk: author for author in Author.objects.all()}
        with self.assertNumQueries(expected_num_queries):
            self.assertEqual(Author.objects.in_bulk(authors), authors)