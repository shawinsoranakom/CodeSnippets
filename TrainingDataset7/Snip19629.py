def test_outer_ref_pk(self):
        subquery = Subquery(Comment.objects.filter(pk=OuterRef("pk")).values("id")[:1])
        tests = [
            ("", 5),
            ("__gt", 0),
            ("__gte", 5),
            ("__lt", 0),
            ("__lte", 5),
        ]
        for lookup, expected_count in tests:
            with self.subTest(f"id{lookup}"):
                queryset = Comment.objects.filter(**{f"id{lookup}": subquery})
                self.assertEqual(queryset.count(), expected_count)