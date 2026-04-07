def test_ticket3739(self):
        # The all() method on querysets returns a copy of the queryset.
        q1 = Tag.objects.order_by("name")
        self.assertIsNot(q1, q1.all())