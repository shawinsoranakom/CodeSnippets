def test_isvalid_lookup(self):
        invalid_geom = fromstr("POLYGON((0 0, 0 1, 1 1, 1 0, 1 1, 1 0, 0 0))")
        State.objects.create(name="invalid", poly=invalid_geom)
        qs = State.objects.all()
        if connection.ops.oracle:
            # Kansas has adjacent vertices with distance 6.99244813842e-12
            # which is smaller than the default Oracle tolerance.
            qs = qs.exclude(name="Kansas")
            self.assertEqual(
                State.objects.filter(name="Kansas", poly__isvalid=False).count(), 1
            )
        self.assertEqual(qs.filter(poly__isvalid=False).count(), 1)
        self.assertEqual(qs.filter(poly__isvalid=True).count(), qs.count() - 1)