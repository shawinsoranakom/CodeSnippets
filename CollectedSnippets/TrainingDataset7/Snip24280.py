def test_covers_lookup(self):
        poly = Polygon(LinearRing((0, 0), (0, 5), (5, 5), (5, 0), (0, 0)))
        state = State.objects.create(name="Test", poly=poly)

        small_poly = Polygon(LinearRing((0, 0), (1, 4), (4, 4), (4, 1), (0, 0)))
        qs = State.objects.filter(poly__covers=small_poly)
        self.assertSequenceEqual(qs, [state])

        large_poly = Polygon(LinearRing((-1, -1), (-1, 6), (6, 6), (6, -1), (-1, -1)))
        qs = State.objects.filter(poly__covers=large_poly)
        self.assertSequenceEqual(qs, [])

        if not connection.ops.oracle:
            # On Oracle, COVERS doesn't match for EQUAL objects.
            qs = State.objects.filter(poly__covers=poly)
            self.assertSequenceEqual(qs, [state])