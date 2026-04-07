def test_pickle(self):
        # Regression for #10197 -- Queries with aggregates can be pickled.
        # First check that pickling is possible at all. No crash = success
        qs = Book.objects.annotate(num_authors=Count("authors"))
        pickle.dumps(qs)

        # Then check that the round trip works.
        query = qs.query.get_compiler(qs.db).as_sql()[0]
        qs2 = pickle.loads(pickle.dumps(qs))
        self.assertEqual(
            qs2.query.get_compiler(qs2.db).as_sql()[0],
            query,
        )