def test_outer_ref_pk_filter_on_pk_comparison(self):
        subquery = Subquery(User.objects.filter(pk=OuterRef("pk")).values("pk")[:1])
        tests = [
            ("gt", 0),
            ("gte", 2),
            ("lt", 0),
            ("lte", 2),
        ]
        for lookup, expected_count in tests:
            with self.subTest(f"pk__{lookup}"):
                qs = Comment.objects.filter(**{f"pk__{lookup}": subquery})
                self.assertEqual(qs.count(), expected_count)