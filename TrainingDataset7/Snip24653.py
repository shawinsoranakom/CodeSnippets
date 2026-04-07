def test_init(self):
        "Testing initialization from valid units"
        d = Distance(m=100)
        self.assertEqual(d.m, 100)

        d1, d2, d3 = D(m=100), D(meter=100), D(metre=100)
        for d in (d1, d2, d3):
            self.assertEqual(d.m, 100)

        d = D(nm=100)
        self.assertEqual(d.m, 185200)

        y1, y2, y3 = D(yd=100), D(yard=100), D(Yard=100)
        for d in (y1, y2, y3):
            self.assertEqual(d.yd, 100)

        mm1, mm2 = D(millimeter=1000), D(MiLLiMeTeR=1000)
        for d in (mm1, mm2):
            self.assertEqual(d.m, 1.0)
            self.assertEqual(d.mm, 1000.0)