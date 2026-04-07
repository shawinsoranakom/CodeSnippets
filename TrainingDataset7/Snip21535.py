def test_filter(self):
        self.assertSequenceEqual(
            Company.objects.filter(~F("based_in_eu")),
            [self.non_eu_company],
        )

        qs = Company.objects.annotate(eu_required=~Value(False))
        self.assertSequenceEqual(
            qs.filter(based_in_eu=F("eu_required")).order_by("eu_required"),
            [self.eu_company],
        )
        self.assertSequenceEqual(
            qs.filter(based_in_eu=~~F("eu_required")),
            [self.eu_company],
        )
        self.assertSequenceEqual(
            qs.filter(based_in_eu=~F("eu_required")),
            [self.non_eu_company],
        )
        self.assertSequenceEqual(qs.filter(based_in_eu=~F("based_in_eu")), [])