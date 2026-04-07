def test_filter_wrapped_lookup_lhs(self):
        qs = (
            Season.objects.annotate(
                before_20=ExpressionWrapper(
                    Q(year__lt=2000),
                    output_field=BooleanField(),
                )
            )
            .filter(before_20=LessThan(F("year"), 1900))
            .values_list("year", flat=True)
        )
        self.assertCountEqual(qs, [1842, 2042])