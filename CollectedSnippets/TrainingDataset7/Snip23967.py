def test_mysql_geodetic_distance_error(self):
        if not connection.ops.mysql:
            self.skipTest("This is a MySQL-specific test.")
        msg = (
            "Only numeric values of degree units are allowed on geodetic distance "
            "queries."
        )
        with self.assertRaisesMessage(ValueError, msg):
            AustraliaCity.objects.filter(
                point__distance_lte=(Point(0, 0), D(m=100))
            ).exists()