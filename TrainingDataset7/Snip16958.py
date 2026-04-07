def test_sum_distinct_aggregate(self):
        """
        Sum on a distinct() QuerySet should aggregate only the distinct items.
        """
        authors = Author.objects.filter(book__in=[self.b5, self.b6])
        self.assertEqual(authors.count(), 3)

        distinct_authors = authors.distinct()
        self.assertEqual(distinct_authors.count(), 2)

        # Selected author ages are 57 and 46
        age_sum = distinct_authors.aggregate(Sum("age"))
        self.assertEqual(age_sum["age__sum"], 103)