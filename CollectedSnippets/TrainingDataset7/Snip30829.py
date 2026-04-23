def test_joined_exclude(self):
        self.assertQuerySetEqual(
            DumbCategory.objects.exclude(namedcategory__name__in=["nonexistent"]),
            [self.nc.pk],
            attrgetter("pk"),
        )