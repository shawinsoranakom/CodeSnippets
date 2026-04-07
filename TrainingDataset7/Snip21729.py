def test_extra_values_distinct_ordering(self):
        t1 = TestObject.objects.create(first="a", second="a", third="a")
        t2 = TestObject.objects.create(first="a", second="b", third="b")
        qs = (
            TestObject.objects.extra(select={"second_extra": "second"})
            .values_list("id", flat=True)
            .distinct()
        )
        self.assertSequenceEqual(qs.order_by("second_extra"), [t1.pk, t2.pk])
        self.assertSequenceEqual(qs.order_by("-second_extra"), [t2.pk, t1.pk])
        # Note: the extra ordering must appear in select clause, so we get two
        # non-distinct results here (this is on purpose, see #7070).
        # Extra select doesn't appear in result values.
        self.assertSequenceEqual(
            qs.order_by("-second_extra").values_list("first"), [("a",), ("a",)]
        )