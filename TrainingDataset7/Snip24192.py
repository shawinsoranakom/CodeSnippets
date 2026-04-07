def test_centroid(self):
        qs = State.objects.exclude(poly__isnull=True).annotate(
            centroid=functions.Centroid("poly")
        )
        tol = (
            1.8 if connection.ops.mysql else (0.1 if connection.ops.oracle else 0.00001)
        )
        for state in qs:
            self.assertTrue(state.poly.centroid.equals_exact(state.centroid, tol))

        with self.assertRaisesMessage(
            TypeError, "'Centroid' takes exactly 1 argument (2 given)"
        ):
            State.objects.annotate(centroid=functions.Centroid("poly", "poly"))