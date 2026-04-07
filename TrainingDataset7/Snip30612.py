def test_ticket9997(self):
        # If a ValuesList or Values queryset is passed as an inner query, we
        # make sure it's only requesting a single value and use that as the
        # thing to select.
        self.assertSequenceEqual(
            Tag.objects.filter(
                name__in=Tag.objects.filter(parent=self.t1).values("name")
            ),
            [self.t2, self.t3],
        )