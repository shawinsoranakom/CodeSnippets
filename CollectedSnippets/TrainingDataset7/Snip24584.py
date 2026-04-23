def test_centroid_collect_filter(self):
        qs = City.objects.annotate(
            parcel_centroid=Centroid(
                Collect(
                    "parcel__center1",
                    filter=~Q(parcel__name__icontains="ignore"),
                )
            )
        )
        city = qs.get(name="Aurora")
        if connection.ops.mariadb:
            self.assertIsNone(city.parcel_centroid)
        else:
            self.assertIsInstance(city.parcel_centroid, Point)
            self.assertAlmostEqual(city.parcel_centroid[0], 3.2128, 4)
            self.assertAlmostEqual(city.parcel_centroid[1], 1.5, 4)