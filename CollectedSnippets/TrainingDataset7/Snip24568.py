def test_related_extent_aggregate(self):
        "Testing the `Extent` aggregate on related geographic models."
        # This combines the Extent and Union aggregates into one query
        aggs = City.objects.aggregate(Extent("location__point"))

        # One for all locations, one that excludes New Mexico (Roswell).
        all_extent = (-104.528056, 29.763374, -79.460734, 40.18476)
        txpa_extent = (-97.516111, 29.763374, -79.460734, 40.18476)
        e1 = City.objects.aggregate(Extent("location__point"))[
            "location__point__extent"
        ]
        e2 = City.objects.exclude(state="NM").aggregate(Extent("location__point"))[
            "location__point__extent"
        ]
        e3 = aggs["location__point__extent"]

        # The tolerance value is to four decimal places because of differences
        # between the Oracle and PostGIS spatial backends on the extent
        # calculation.
        tol = 4
        for ref, e in [(all_extent, e1), (txpa_extent, e2), (all_extent, e3)]:
            for ref_val, e_val in zip(ref, e):
                self.assertAlmostEqual(ref_val, e_val, tol)