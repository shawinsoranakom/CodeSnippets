def test_union_filter(self):
        qs = City.objects.annotate(
            parcel_point_union=Union(
                "parcel__center2",
                filter=~Q(parcel__name__icontains="ignore"),
            ),
            parcel_point_nonexistent=Union(
                "parcel__center2",
                filter=Q(parcel__name__icontains="nonexistent"),
            ),
            parcel_point_union_single=Union(
                "parcel__center2",
                filter=Q(parcel__name__contains="Alpha"),
            ),
        )
        city = qs.get(name="Aurora")
        self.assertIn(
            city.parcel_point_union.wkt,
            [
                GEOSGeometry("MULTIPOINT (12.75 10.05, 3.7128 -5.006)"),
                GEOSGeometry("MULTIPOINT (3.7128 -5.006, 12.75 10.05)"),
            ],
        )
        self.assertIsNone(city.parcel_point_nonexistent)
        self.assertEqual(city.parcel_point_union_single.wkt, "POINT (3.7128 -5.006)")