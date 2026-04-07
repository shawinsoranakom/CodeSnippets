def test_make_valid(self):
        invalid_geom = fromstr("POLYGON((0 0, 0 1, 1 1, 1 0, 1 1, 1 0, 0 0))")
        State.objects.create(name="invalid", poly=invalid_geom)
        invalid = (
            State.objects.filter(name="invalid")
            .annotate(repaired=functions.MakeValid("poly"))
            .first()
        )
        self.assertIs(invalid.repaired.valid, True)
        self.assertTrue(
            invalid.repaired.equals(
                fromstr("POLYGON((0 0, 0 1, 1 1, 1 0, 0 0))", srid=invalid.poly.srid)
            )
        )