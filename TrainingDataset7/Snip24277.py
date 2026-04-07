def test_null_geometries_excluded_in_lookups(self):
        """NULL features are excluded in spatial lookup functions."""
        null = State.objects.create(name="NULL", poly=None)
        queries = [
            ("equals", Point(1, 1)),
            ("disjoint", Point(1, 1)),
            ("touches", Point(1, 1)),
            ("crosses", LineString((0, 0), (1, 1), (5, 5))),
            ("within", Point(1, 1)),
            ("overlaps", LineString((0, 0), (1, 1), (5, 5))),
            ("contains", LineString((0, 0), (1, 1), (5, 5))),
            ("intersects", LineString((0, 0), (1, 1), (5, 5))),
            ("relate", (Point(1, 1), "T*T***FF*")),
            ("same_as", Point(1, 1)),
            ("exact", Point(1, 1)),
            ("coveredby", Point(1, 1)),
            ("covers", Point(1, 1)),
        ]
        for lookup, geom in queries:
            with self.subTest(lookup=lookup):
                self.assertNotIn(
                    null, State.objects.filter(**{"poly__%s" % lookup: geom})
                )