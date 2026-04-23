def test_ticket7235(self):
        # An EmptyQuerySet should not raise exceptions if it is filtered.
        Eaten.objects.create(meal="m")
        q = Eaten.objects.none()
        with self.assertNumQueries(0):
            self.assertSequenceEqual(q.all(), [])
            self.assertSequenceEqual(q.filter(meal="m"), [])
            self.assertSequenceEqual(q.exclude(meal="m"), [])
            self.assertSequenceEqual(q.complex_filter({"pk": 1}), [])
            self.assertSequenceEqual(q.select_related("food"), [])
            self.assertSequenceEqual(q.annotate(Count("food")), [])
            self.assertSequenceEqual(q.order_by("meal", "food"), [])
            self.assertSequenceEqual(q.distinct(), [])
            self.assertSequenceEqual(q.extra(select={"foo": "1"}), [])
            self.assertSequenceEqual(q.reverse(), [])
            q.query.low_mark = 1
            msg = "Cannot change a query once a slice has been taken."
            with self.assertRaisesMessage(TypeError, msg):
                q.extra(select={"foo": "1"})
            self.assertSequenceEqual(q.defer("meal"), [])
            self.assertSequenceEqual(q.only("meal"), [])