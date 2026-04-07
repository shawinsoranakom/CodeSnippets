def test02_distance_lookup(self):
        "Testing distance lookup support on non-point geography fields."
        z = Zipcode.objects.get(code="77002")
        cities1 = list(
            City.objects.filter(point__distance_lte=(z.poly, D(mi=500)))
            .order_by("name")
            .values_list("name", flat=True)
        )
        cities2 = list(
            City.objects.filter(point__dwithin=(z.poly, D(mi=500)))
            .order_by("name")
            .values_list("name", flat=True)
        )
        for cities in [cities1, cities2]:
            self.assertEqual(["Dallas", "Houston", "Oklahoma City"], cities)