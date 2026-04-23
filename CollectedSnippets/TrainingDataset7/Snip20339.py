def test_empty_queryset(self):
        Author.objects.create(name="John Smith")
        queryset = Author.objects.values("id")
        tests = [
            (queryset.none(), "QuerySet.none()"),
            (queryset.filter(id=0), "QuerySet.filter(id=0)"),
            (Subquery(queryset.none()), "Subquery(QuerySet.none())"),
            (Subquery(queryset.filter(id=0)), "Subquery(Queryset.filter(id=0)"),
        ]
        for empty_query, description in tests:
            with self.subTest(description), self.assertNumQueries(1):
                qs = Author.objects.annotate(annotation=Coalesce(empty_query, 42))
                self.assertEqual(qs.first().annotation, 42)