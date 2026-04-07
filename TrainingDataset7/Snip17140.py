def test_filter_aggregates_or_connector(self):
        q1 = Q(price__gt=50)
        q2 = Q(authors__count__gt=1)
        query = Book.objects.annotate(Count("authors")).filter(q1 | q2).order_by("pk")
        self.assertQuerySetEqual(
            query,
            [self.b1.pk, self.b4.pk, self.b5.pk, self.b6.pk],
            attrgetter("pk"),
        )