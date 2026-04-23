def test_addition(self):
        "Test addition & subtraction"
        d1 = D(m=100)
        d2 = D(m=200)

        d3 = d1 + d2
        self.assertEqual(d3.m, 300)
        d3 += d1
        self.assertEqual(d3.m, 400)

        d4 = d1 - d2
        self.assertEqual(d4.m, -100)
        d4 -= d1
        self.assertEqual(d4.m, -200)

        with self.assertRaises(TypeError):
            d1 + 1

        with self.assertRaises(TypeError):
            d1 - 1

        with self.assertRaises(TypeError):
            d1 += 1

        with self.assertRaises(TypeError):
            d1 -= 1