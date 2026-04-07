def test_hectare(self):
        a = A(sq_m=10000)
        self.assertEqual(a.ha, 1)