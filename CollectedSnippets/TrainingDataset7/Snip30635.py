def test_ticket_20250(self):
        # A negated Q along with an annotated queryset failed in Django 1.4
        qs = Author.objects.annotate(Count("item"))
        qs = qs.filter(~Q(extra__value=0)).order_by("name")

        self.assertIn("SELECT", str(qs.query))
        self.assertSequenceEqual(qs, [self.a1, self.a2, self.a3, self.a4])