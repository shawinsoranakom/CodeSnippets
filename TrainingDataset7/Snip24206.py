def test_area_lookups(self):
        # Create projected countries so the test works on all backends.
        CountryWebMercator.objects.bulk_create(
            CountryWebMercator(name=c.name, mpoly=c.mpoly.transform(3857, clone=True))
            for c in Country.objects.all()
        )
        qs = CountryWebMercator.objects.annotate(area=functions.Area("mpoly"))
        self.assertEqual(
            qs.get(area__lt=Area(sq_km=500000)),
            CountryWebMercator.objects.get(name="New Zealand"),
        )

        with self.assertRaisesMessage(
            ValueError, "AreaField only accepts Area measurement objects."
        ):
            qs.get(area__lt=500000)