def test_extent_filter(self):
        qs = City.objects.annotate(
            parcel_border=Extent(
                "parcel__border1",
                filter=~Q(parcel__name__icontains="ignore"),
            ),
            parcel_border_nonexistent=Extent(
                "parcel__border1",
                filter=Q(parcel__name__icontains="nonexistent"),
            ),
            parcel_border_no_filter=Extent("parcel__border1"),
        )
        city = qs.get(name="Aurora")
        self.assertEqual(city.parcel_border, (0.0, 0.0, 22.0, 22.0))
        self.assertIsNone(city.parcel_border_nonexistent)
        self.assertEqual(city.parcel_border_no_filter, (0.0, 0.0, 32.0, 32.0))