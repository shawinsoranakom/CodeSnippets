def test_strictly_above_below_lookups(self):
        dallas = City.objects.get(name="Dallas")
        self.assertQuerySetEqual(
            City.objects.filter(point__strictly_above=dallas.point).order_by("name"),
            ["Chicago", "Lawrence", "Oklahoma City", "Pueblo", "Victoria"],
            lambda b: b.name,
        )
        self.assertQuerySetEqual(
            City.objects.filter(point__strictly_below=dallas.point).order_by("name"),
            ["Houston", "Wellington"],
            lambda b: b.name,
        )