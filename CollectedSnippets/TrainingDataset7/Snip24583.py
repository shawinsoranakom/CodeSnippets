def test_collect_filter(self):
        qs = City.objects.annotate(
            parcel_center=Collect(
                "parcel__center1",
                filter=~Q(parcel__name__icontains="ignore"),
            ),
            parcel_center_nonexistent=Collect(
                "parcel__center1",
                filter=Q(parcel__name__icontains="nonexistent"),
            ),
            parcel_center_single=Collect(
                "parcel__center1",
                filter=Q(parcel__name__contains="Alpha"),
            ),
        )
        city = qs.get(name="Aurora")
        self.assertEqual(
            city.parcel_center.wkt,
            GEOSGeometry("MULTIPOINT (1.7128 -2.006, 4.7128 5.006)"),
        )
        self.assertIsNone(city.parcel_center_nonexistent)
        self.assertIn(
            city.parcel_center_single.wkt,
            [
                GEOSGeometry("MULTIPOINT (1.7128 -2.006)"),
                GEOSGeometry("POINT (1.7128 -2.006)"),  # SpatiaLite collapse to POINT.
            ],
        )