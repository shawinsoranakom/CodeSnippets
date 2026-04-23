def test_make_valid_multipolygon(self):
        invalid_geom = fromstr(
            "POLYGON((0 0, 0 1 , 1 1 , 1 0, 0 0), (10 0, 10 1, 11 1, 11 0, 10 0))"
        )
        State.objects.create(name="invalid", poly=invalid_geom)
        invalid = (
            State.objects.filter(name="invalid")
            .annotate(
                repaired=functions.MakeValid("poly"),
            )
            .get()
        )
        self.assertIs(invalid.repaired.valid, True)
        self.assertTrue(
            invalid.repaired.equals(
                fromstr(
                    "MULTIPOLYGON (((0 0, 0 1, 1 1, 1 0, 0 0)), "
                    "((10 0, 10 1, 11 1, 11 0, 10 0)))",
                    srid=invalid.poly.srid,
                )
            )
        )
        self.assertEqual(len(invalid.repaired), 2)