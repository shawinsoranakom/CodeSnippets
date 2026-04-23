def test_non_grouped_annotation_not_in_group_by(self):
        """
        An annotation not included in values() before an aggregate should be
        excluded from the group by clause.
        """
        qs = (
            Book.objects.annotate(xprice=F("price"))
            .filter(rating=4.0)
            .values("rating")
            .annotate(count=Count("publisher_id", distinct=True))
            .values("count", "rating")
            .order_by("count")
        )
        self.assertEqual(list(qs), [{"rating": 4.0, "count": 2}])