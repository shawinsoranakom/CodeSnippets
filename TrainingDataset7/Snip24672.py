def test_multiplication(self):
        "Test multiplication & division"
        a1 = A(sq_m=100)

        a3 = a1 * 2
        self.assertEqual(a3.sq_m, 200)
        a3 = 2 * a1
        self.assertEqual(a3.sq_m, 200)
        a3 *= 5
        self.assertEqual(a3.sq_m, 1000)

        a4 = a1 / 2
        self.assertEqual(a4.sq_m, 50)
        a4 /= 5
        self.assertEqual(a4.sq_m, 10)

        with self.assertRaises(TypeError):
            a1 * A(sq_m=1)

        with self.assertRaises(TypeError):
            a1 *= A(sq_m=1)

        with self.assertRaises(TypeError):
            a1 / A(sq_m=1)

        with self.assertRaises(TypeError):
            a1 /= A(sq_m=1)