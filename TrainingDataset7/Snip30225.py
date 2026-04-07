def test_child_link_prefetch(self):
        with self.assertNumQueries(2):
            authors = [
                a.authorwithage
                for a in Author.objects.prefetch_related("authorwithage")
            ]

        # Regression for #18090: the prefetching query must include an IN
        # clause. Note that on Oracle the table name is upper case in the
        # generated SQL, thus the .lower() call.
        self.assertIn("authorwithage", connection.queries[-1]["sql"].lower())
        self.assertIn(" IN ", connection.queries[-1]["sql"])

        self.assertEqual(authors, [a.authorwithage for a in Author.objects.all()])