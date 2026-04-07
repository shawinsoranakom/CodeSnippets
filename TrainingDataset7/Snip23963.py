def test_distance_lookups(self):
        # Retrieving the cities within a 20km 'donut' w/a 7km radius 'hole'
        # (thus, Houston and Southside place will be excluded as tested in
        # the `test02_dwithin` above).
        for model in [SouthTexasCity, SouthTexasCityFt]:
            stx_pnt = self.stx_pnt.transform(
                model._meta.get_field("point").srid, clone=True
            )
            qs = model.objects.filter(point__distance_gte=(stx_pnt, D(km=7))).filter(
                point__distance_lte=(stx_pnt, D(km=20)),
            )
            cities = self.get_names(qs)
            self.assertEqual(cities, ["Bellaire", "Pearland", "West University Place"])

        # Doing a distance query using Polygons instead of a Point.
        z = SouthTexasZipcode.objects.get(name="77005")
        qs = SouthTexasZipcode.objects.exclude(name="77005").filter(
            poly__distance_lte=(z.poly, D(m=275))
        )
        self.assertEqual(["77025", "77401"], self.get_names(qs))
        # If we add a little more distance 77002 should be included.
        qs = SouthTexasZipcode.objects.exclude(name="77005").filter(
            poly__distance_lte=(z.poly, D(m=300))
        )
        self.assertEqual(["77002", "77025", "77401"], self.get_names(qs))