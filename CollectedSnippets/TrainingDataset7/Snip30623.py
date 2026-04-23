def test_double_exclude(self):
        self.assertQuerySetEqual(
            Item.objects.filter(Q(tags__name="t4")),
            Item.objects.filter(~~Q(tags__name="t4")),
        )
        self.assertQuerySetEqual(
            Item.objects.filter(Q(tags__name="t4")),
            Item.objects.filter(~Q(~Q(tags__name="t4"))),
        )