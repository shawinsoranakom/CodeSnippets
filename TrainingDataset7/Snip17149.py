def test_annotate_distinct_aggregate(self):
        # There are three books with rating of 4.0 and two of the books have
        # the same price. Hence, the distinct removes one rating of 4.0
        # from the results.
        vals1 = (
            Book.objects.values("rating", "price")
            .distinct()
            .aggregate(result=Sum("rating"))
        )
        vals2 = Book.objects.aggregate(result=Sum("rating") - Value(4.0))
        self.assertEqual(vals1, vals2)