def test_distance_lookups_with_expression_rhs(self):
        stx_pnt = self.stx_pnt.transform(
            SouthTexasCity._meta.get_field("point").srid, clone=True
        )
        qs = SouthTexasCity.objects.filter(
            point__distance_lte=(stx_pnt, F("radius")),
        ).order_by("name")
        self.assertEqual(
            self.get_names(qs),
            [
                "Bellaire",
                "Downtown Houston",
                "Southside Place",
                "West University Place",
            ],
        )

        # With a combined expression
        qs = SouthTexasCity.objects.filter(
            point__distance_lte=(stx_pnt, F("radius") * 2),
        ).order_by("name")
        self.assertEqual(len(qs), 5)
        self.assertIn("Pearland", self.get_names(qs))

        # With spheroid param
        if connection.features.supports_distance_geodetic:
            hobart = AustraliaCity.objects.get(name="Hobart")
            AustraliaCity.objects.update(ref_point=hobart.point)
            for ref_point in [hobart.point, F("ref_point")]:
                qs = AustraliaCity.objects.filter(
                    point__distance_lte=(ref_point, F("radius") * 70, "spheroid"),
                ).order_by("name")
                self.assertEqual(
                    self.get_names(qs), ["Canberra", "Hobart", "Melbourne"]
                )

        # With a complex geometry expression
        self.assertFalse(
            SouthTexasCity.objects.filter(
                point__distance_gt=(Union("point", "point"), 0)
            )
        )
        self.assertEqual(
            SouthTexasCity.objects.filter(
                point__distance_lte=(Union("point", "point"), 0)
            ).count(),
            SouthTexasCity.objects.count(),
        )