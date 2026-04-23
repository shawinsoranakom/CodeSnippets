def test_exclude_in(self):
        self.assertQuerySetEqual(
            Item.objects.exclude(Q(tags__name__in=["t4", "t3"])),
            Item.objects.filter(~Q(tags__name__in=["t4", "t3"])),
        )
        self.assertQuerySetEqual(
            Item.objects.filter(Q(tags__name__in=["t4", "t3"])),
            Item.objects.filter(~~Q(tags__name__in=["t4", "t3"])),
        )