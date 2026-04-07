def test_referenced_subquery_requires_wrapping(self):
        total_books_qs = (
            Author.book_set.through.objects.values("author")
            .filter(author=OuterRef("pk"))
            .annotate(total=Count("book"))
        )
        with self.assertNumQueries(1) as ctx:
            aggregate = (
                Author.objects.annotate(
                    total_books=Subquery(total_books_qs.values("total"))
                )
                .values("pk", "total_books")
                .aggregate(
                    sum_total_books=Sum("total_books"),
                )
            )
        sql = ctx.captured_queries[0]["sql"].lower()
        self.assertEqual(sql.count("select"), 3, "Subquery wrapping required")
        self.assertEqual(aggregate, {"sum_total_books": 3})