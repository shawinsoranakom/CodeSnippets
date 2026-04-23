def test_unicode_date(self):
        "Testing dates are converted properly, even on SpatiaLite. See #16408."
        founded = datetime(1857, 5, 23)
        PennsylvaniaCity.objects.create(
            name="Mansfield",
            county="Tioga",
            point="POINT(-77.071445 41.823881)",
            founded=founded,
        )
        self.assertEqual(
            founded, PennsylvaniaCity.objects.datetimes("founded", "day")[0]
        )
        self.assertEqual(
            founded, PennsylvaniaCity.objects.aggregate(Min("founded"))["founded__min"]
        )