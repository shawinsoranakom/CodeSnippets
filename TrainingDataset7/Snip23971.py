def test_area(self):
        # Reference queries:
        # SELECT ST_Area(poly) FROM distapp_southtexaszipcode;
        area_sq_m = [
            5437908.90234375,
            10183031.4389648,
            11254471.0073242,
            9881708.91772461,
        ]
        # Tolerance has to be lower for Oracle
        tol = 2
        for i, z in enumerate(
            SouthTexasZipcode.objects.annotate(area=Area("poly")).order_by("name")
        ):
            self.assertAlmostEqual(area_sq_m[i], z.area.sq_m, tol)