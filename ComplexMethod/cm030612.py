def powtest(self, type):
        if type != float:
            for i in range(-1000, 1000):
                self.assertEqual(pow(type(i), 0), 1)
                self.assertEqual(pow(type(i), 1), type(i))
                self.assertEqual(pow(type(0), 1), type(0))
                self.assertEqual(pow(type(1), 1), type(1))

            for i in range(-100, 100):
                self.assertEqual(pow(type(i), 3), i*i*i)

            pow2 = 1
            for i in range(0, 31):
                self.assertEqual(pow(2, i), pow2)
                if i != 30 : pow2 = pow2*2

            for i in list(range(-10, 0)) + list(range(1, 10)):
                ii = type(i)
                inv = pow(ii, -1) # inverse of ii
                for jj in range(-10, 0):
                    self.assertAlmostEqual(pow(ii, jj), pow(inv, -jj))

        for othertype in int, float:
            for i in range(1, 100):
                zero = type(0)
                exp = -othertype(i/10.0)
                if exp == 0:
                    continue
                self.assertRaises(ZeroDivisionError, pow, zero, exp)

        il, ih = -20, 20
        jl, jh = -5,   5
        kl, kh = -10, 10
        asseq = self.assertEqual
        if type == float:
            il = 1
            asseq = self.assertAlmostEqual
        elif type == int:
            jl = 0
        elif type == int:
            jl, jh = 0, 15
        for i in range(il, ih+1):
            for j in range(jl, jh+1):
                for k in range(kl, kh+1):
                    if k != 0:
                        if type == float or j < 0:
                            self.assertRaises(TypeError, pow, type(i), j, k)
                            continue
                        asseq(
                            pow(type(i),j,k),
                            pow(type(i),j)% type(k)
                        )