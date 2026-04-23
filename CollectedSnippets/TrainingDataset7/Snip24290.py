def test_unionagg_tolerance_escaping(self):
        tx = Country.objects.get(name="Texas").mpoly
        with self.assertRaises(DatabaseError):
            City.objects.filter(point__within=tx).aggregate(
                Union("point", tolerance="0.05))), (((1"),
            )