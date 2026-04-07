def test_grouped_annotation_in_group_by(self):
        """
        An annotation included in values() before an aggregate should be
        included in the group by clause.
        """
        qs = (
            Book.objects.annotate(xprice=F("price"))
            .filter(rating=4.0)
            .values("rating", "xprice")
            .annotate(count=Count("publisher_id", distinct=True))
            .values("count", "rating")
            .order_by("count")
        )
        self.assertEqual(
            list(qs),
            [
                {"rating": 4.0, "count": 1},
                {"rating": 4.0, "count": 2},
            ],
        )