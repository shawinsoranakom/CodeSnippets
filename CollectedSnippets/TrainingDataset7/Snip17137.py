def test_negated_aggregation(self):
        expected_results = Author.objects.exclude(
            pk__in=Author.objects.annotate(book_cnt=Count("book")).filter(book_cnt=2)
        ).order_by("name")
        expected_results = [a.name for a in expected_results]
        qs = (
            Author.objects.annotate(book_cnt=Count("book"))
            .exclude(Q(book_cnt=2), Q(book_cnt=2))
            .order_by("name")
        )
        self.assertQuerySetEqual(qs, expected_results, lambda b: b.name)
        expected_results = Author.objects.exclude(
            pk__in=Author.objects.annotate(book_cnt=Count("book")).filter(book_cnt=2)
        ).order_by("name")
        expected_results = [a.name for a in expected_results]
        qs = (
            Author.objects.annotate(book_cnt=Count("book"))
            .exclude(Q(book_cnt=2) | Q(book_cnt=2))
            .order_by("name")
        )
        self.assertQuerySetEqual(qs, expected_results, lambda b: b.name)