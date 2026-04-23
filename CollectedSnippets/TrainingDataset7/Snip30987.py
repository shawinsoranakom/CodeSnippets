def test_get_item(self):
        # Indexing on RawQuerySets
        query = "SELECT * FROM raw_query_author ORDER BY id ASC"
        third_author = Author.objects.raw(query)[2]
        self.assertEqual(third_author.first_name, "Bob")

        first_two = Author.objects.raw(query)[0:2]
        self.assertEqual(len(first_two), 2)

        with self.assertRaises(TypeError):
            Author.objects.raw(query)["test"]