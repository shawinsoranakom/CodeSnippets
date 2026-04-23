def test_copy(self):
        "Testing use with the Python `copy` module."
        import copy

        poly = GEOSGeometry(
            "POLYGON((0 0, 0 23, 23 23, 23 0, 0 0), (5 5, 5 10, 10 10, 10 5, 5 5))"
        )
        cpy1 = copy.copy(poly)
        cpy2 = copy.deepcopy(poly)
        self.assertNotEqual(poly._ptr, cpy1._ptr)
        self.assertNotEqual(poly._ptr, cpy2._ptr)