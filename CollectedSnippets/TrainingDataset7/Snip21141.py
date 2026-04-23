def test_fast_delete_aggregation(self):
        # Fast-deleting when filtering against an aggregation result in
        # a single query containing a subquery.
        Base.objects.create()
        with self.assertNumQueries(1):
            self.assertEqual(
                Base.objects.annotate(
                    rels_count=models.Count("rels"),
                )
                .filter(rels_count=0)
                .delete(),
                (1, {"delete.Base": 1}),
            )
        self.assertIs(Base.objects.exists(), False)