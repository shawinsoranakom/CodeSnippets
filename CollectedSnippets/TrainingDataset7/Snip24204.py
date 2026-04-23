def test_isvalid(self):
        valid_geom = fromstr("POLYGON((0 0, 0 1, 1 1, 1 0, 0 0))")
        invalid_geom = fromstr("POLYGON((0 0, 0 1, 1 1, 1 0, 1 1, 1 0, 0 0))")
        State.objects.create(name="valid", poly=valid_geom)
        State.objects.create(name="invalid", poly=invalid_geom)
        valid = (
            State.objects.filter(name="valid")
            .annotate(isvalid=functions.IsValid("poly"))
            .first()
        )
        invalid = (
            State.objects.filter(name="invalid")
            .annotate(isvalid=functions.IsValid("poly"))
            .first()
        )
        self.assertIs(valid.isvalid, True)
        self.assertIs(invalid.isvalid, False)