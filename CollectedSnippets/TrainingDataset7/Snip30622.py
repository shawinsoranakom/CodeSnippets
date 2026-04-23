def test_nested_exclude(self):
        self.assertQuerySetEqual(
            Item.objects.exclude(~Q(tags__name="t4")),
            Item.objects.filter(~~Q(tags__name="t4")),
        )