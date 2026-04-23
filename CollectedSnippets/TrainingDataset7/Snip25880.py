def test_filter_exists_lhs(self):
        qs = Season.objects.annotate(
            before_20=Exists(
                Season.objects.filter(pk=OuterRef("pk"), year__lt=2000),
            )
        ).filter(before_20=LessThan(F("year"), 1900))
        self.assertCountEqual(qs, [self.s2, self.s3])