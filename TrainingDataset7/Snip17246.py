def test_order_by_alias_aggregate(self):
        qs = (
            Author.objects.values("age")
            .alias(age_count=Count("age"))
            .order_by("age_count", "age")
        )
        self.assertIs(hasattr(qs.first(), "age_count"), False)
        self.assertQuerySetEqual(qs, [35, 46, 57, 34], lambda a: a["age"])