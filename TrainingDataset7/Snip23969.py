def test_dwithin_with_expression_rhs(self):
        # LineString of Wollongong and Adelaide coords.
        ls = LineString(((150.902, -34.4245), (138.6, -34.9258)), srid=4326)
        qs = AustraliaCity.objects.filter(
            point__dwithin=(ls, F("allowed_distance")),
        ).order_by("name")
        self.assertEqual(
            self.get_names(qs),
            ["Adelaide", "Mittagong", "Shellharbour", "Thirroul", "Wollongong"],
        )