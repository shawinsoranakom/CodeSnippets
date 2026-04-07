def test_exclude(self):
        self.assertQuerySetEqual(
            Item.objects.exclude(tags__name="t4"),
            Item.objects.filter(~Q(tags__name="t4")),
        )
        self.assertQuerySetEqual(
            Item.objects.exclude(Q(tags__name="t4") | Q(tags__name="t3")),
            Item.objects.filter(~(Q(tags__name="t4") | Q(tags__name="t3"))),
        )
        self.assertQuerySetEqual(
            Item.objects.exclude(Q(tags__name="t4") | ~Q(tags__name="t3")),
            Item.objects.filter(~(Q(tags__name="t4") | ~Q(tags__name="t3"))),
        )