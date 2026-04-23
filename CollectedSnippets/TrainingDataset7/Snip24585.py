def test_make_line_filter(self):
        qs = City.objects.annotate(
            parcel_line=MakeLine(
                "parcel__center1",
                filter=~Q(parcel__name__icontains="ignore"),
            ),
            parcel_line_nonexistent=MakeLine(
                "parcel__center1",
                filter=Q(parcel__name__icontains="nonexistent"),
            ),
        )
        city = qs.get(name="Aurora")
        self.assertIn(
            city.parcel_line.wkt,
            # The default ordering is flaky, so check both.
            [
                "LINESTRING (1.7128 -2.006, 4.7128 5.006)",
                "LINESTRING (4.7128 5.006, 1.7128 -2.006)",
            ],
        )
        self.assertIsNone(city.parcel_line_nonexistent)