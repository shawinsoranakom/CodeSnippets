def test_init(self):
        "Testing initialization from valid units"
        a = Area(sq_m=100)
        self.assertEqual(a.sq_m, 100)

        a = A(sq_m=100)
        self.assertEqual(a.sq_m, 100)

        a = A(sq_mi=100)
        self.assertEqual(a.sq_m, 258998811.0336)