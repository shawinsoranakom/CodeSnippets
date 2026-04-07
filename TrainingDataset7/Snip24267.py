def test_disjoint_lookup(self):
        "Testing the `disjoint` lookup type."
        ptown = City.objects.get(name="Pueblo")
        qs1 = City.objects.filter(point__disjoint=ptown.point)
        self.assertEqual(7, qs1.count())
        qs2 = State.objects.filter(poly__disjoint=ptown.point)
        self.assertEqual(1, qs2.count())
        self.assertEqual("Kansas", qs2[0].name)