def test_having_group_by(self):
        # When a field occurs on the LHS of a HAVING clause that it
        # appears correctly in the GROUP BY clause
        qs = (
            Book.objects.values_list("name")
            .annotate(n_authors=Count("authors"))
            .filter(pages__gt=F("n_authors"))
            .values_list("name", flat=True)
            .order_by("name")
        )
        # Results should be the same, all Books have more pages than authors
        self.assertEqual(list(qs), list(Book.objects.values_list("name", flat=True)))