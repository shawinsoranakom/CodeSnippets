def test_dwithin_with_expression_rhs_not_supported(self):
        ls = LineString(((150.902, -34.4245), (138.6, -34.9258)), srid=4326)
        msg = (
            "This backend does not support expressions for specifying "
            "distance in the dwithin lookup."
        )
        with self.assertRaisesMessage(NotSupportedError, msg):
            list(
                AustraliaCity.objects.filter(
                    point__dwithin=(ls, F("allowed_distance")),
                )
            )