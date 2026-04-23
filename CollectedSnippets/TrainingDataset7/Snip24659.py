def test_multiplication(self):
        "Test multiplication & division"
        d1 = D(m=100)

        d3 = d1 * 2
        self.assertEqual(d3.m, 200)
        d3 = 2 * d1
        self.assertEqual(d3.m, 200)
        d3 *= 5
        self.assertEqual(d3.m, 1000)

        d4 = d1 / 2
        self.assertEqual(d4.m, 50)
        d4 /= 5
        self.assertEqual(d4.m, 10)
        d5 = d1 / D(m=2)
        self.assertEqual(d5, 50)

        a5 = d1 * D(m=10)
        self.assertIsInstance(a5, Area)
        self.assertEqual(a5.sq_m, 100 * 10)

        with self.assertRaises(TypeError):
            d1 *= D(m=1)

        with self.assertRaises(TypeError):
            d1 /= D(m=1)