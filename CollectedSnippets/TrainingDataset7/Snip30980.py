def test_missing_fields(self):
        query = "SELECT id, first_name, dob FROM raw_query_author"
        for author in Author.objects.raw(query):
            self.assertIsNotNone(author.first_name)
            # last_name isn't given, but it will be retrieved on demand
            self.assertIsNotNone(author.last_name)