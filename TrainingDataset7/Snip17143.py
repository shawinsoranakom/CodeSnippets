def test_filter_aggregates_negated_xor_connector(self):
        q1 = Q(price__gt=50)
        q2 = Q(authors__count__gt=1)
        query = (
            Book.objects.annotate(Count("authors")).filter(~(q1 ^ q2)).order_by("pk")
        )
        self.assertQuerySetEqual(
            query,
            [self.b2.pk, self.b3.pk, self.b5.pk],
            attrgetter("pk"),
        )