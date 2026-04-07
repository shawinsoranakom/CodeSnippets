def test_equals_identical(self):
        tests = [
            # Empty inputs of different types are not equals_identical.
            ("POINT EMPTY", "LINESTRING EMPTY", False),
            # Empty inputs of different dimensions are not equals_identical.
            ("POINT EMPTY", "POINT Z EMPTY", False),
            # Non-empty inputs of different dimensions are not
            # equals_identical.
            ("POINT Z (1 2 3)", "POINT M (1 2 3)", False),
            ("POINT ZM (1 2 3 4)", "POINT Z (1 2 3)", False),
            # Inputs with different structure are not equals_identical.
            ("LINESTRING (1 1, 2 2)", "MULTILINESTRING ((1 1, 2 2))", False),
            # Inputs with different types are not equals_identical.
            (
                "GEOMETRYCOLLECTION (LINESTRING (1 1, 2 2))",
                "MULTILINESTRING ((1 1, 2 2))",
                False,
            ),
            # Same lines are equals_identical.
            ("LINESTRING M (1 1 0, 2 2 1)", "LINESTRING M (1 1 0, 2 2 1)", True),
            # Different lines are not equals_identical.
            ("LINESTRING M (1 1 0, 2 2 1)", "LINESTRING M (1 1 1, 2 2 1)", False),
            # Same polygons are equals_identical.
            ("POLYGON ((0 0, 1 0, 1 1, 0 0))", "POLYGON ((0 0, 1 0, 1 1, 0 0))", True),
            # Different polygons are not equals_identical.
            ("POLYGON ((0 0, 1 0, 1 1, 0 0))", "POLYGON ((1 0, 1 1, 0 0, 1 0))", False),
            # Different polygons (number of holes) are not equals_identical.
            (
                "POLYGON ((0 0, 10 0, 10 10, 0 10, 0 0), (1 1, 2 1, 2 2, 1 1))",
                (
                    "POLYGON ((0 0, 10 0, 10 10, 0 10, 0 0), (1 1, 2 1, 2 2, 1 1), "
                    "(3 3, 4 3, 4 4, 3 3))"
                ),
                False,
            ),
            # Same collections are equals_identical.
            (
                "MULTILINESTRING ((1 1, 2 2), (2 2, 3 3))",
                "MULTILINESTRING ((1 1, 2 2), (2 2, 3 3))",
                True,
            ),
            # Different collections (structure) are not equals_identical.
            (
                "MULTILINESTRING ((1 1, 2 2), (2 2, 3 3))",
                "MULTILINESTRING ((2 2, 3 3), (1 1, 2 2))",
                False,
            ),
        ]
        for g1, g2, is_equal_identical in tests:
            with self.subTest(g1=g1, g2=g2):
                self.assertIs(
                    fromstr(g1).equals_identical(fromstr(g2)), is_equal_identical
                )