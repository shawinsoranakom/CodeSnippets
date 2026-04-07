def test_direct_exclude(self):
        self.assertQuerySetEqual(
            NamedCategory.objects.exclude(name__in=["nonexistent"]),
            [self.nc.pk],
            attrgetter("pk"),
        )