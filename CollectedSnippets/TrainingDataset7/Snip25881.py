def test_filter_subquery_lhs(self):
        qs = Season.objects.annotate(
            before_20=Subquery(
                Season.objects.filter(pk=OuterRef("pk")).values(
                    lesser=LessThan(F("year"), 2000),
                ),
            )
        ).filter(before_20=LessThan(F("year"), 1900))
        self.assertCountEqual(qs, [self.s2, self.s3])