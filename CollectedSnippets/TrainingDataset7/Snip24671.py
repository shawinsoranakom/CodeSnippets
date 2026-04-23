def test_addition(self):
        "Test addition & subtraction"
        a1 = A(sq_m=100)
        a2 = A(sq_m=200)

        a3 = a1 + a2
        self.assertEqual(a3.sq_m, 300)
        a3 += a1
        self.assertEqual(a3.sq_m, 400)

        a4 = a1 - a2
        self.assertEqual(a4.sq_m, -100)
        a4 -= a1
        self.assertEqual(a4.sq_m, -200)

        with self.assertRaises(TypeError):
            a1 + 1

        with self.assertRaises(TypeError):
            a1 - 1

        with self.assertRaises(TypeError):
            a1 += 1

        with self.assertRaises(TypeError):
            a1 -= 1