def test_missing_fields_fetch_mode_peers(self):
        query = "SELECT id, first_name, dob FROM raw_query_author"
        authors = list(Author.objects.fetch_mode(FETCH_PEERS).raw(query))
        with self.assertNumQueries(1):
            authors[0].last_name
            authors[1].last_name