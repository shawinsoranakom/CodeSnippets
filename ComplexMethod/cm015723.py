def test_truediv(self):
        simple_real = [float(i) for i in range(-5, 6)]
        simple_complex = [complex(x, y) for x in simple_real for y in simple_real]
        for x in simple_complex:
            for y in simple_complex:
                self.check_div(x, y)

        # A naive complex division algorithm (such as in 2.0) is very prone to
        # nonsense errors for these (overflows and underflows).
        self.check_div(complex(1e200, 1e200), 1+0j)
        self.check_div(complex(1e-200, 1e-200), 1+0j)

        # Just for fun.
        for i in range(100):
            self.check_div(complex(random(), random()),
                           complex(random(), random()))

        self.assertAlmostEqual(complex.__truediv__(2+0j, 1+1j), 1-1j)
        self.assertRaises(TypeError, operator.truediv, 1j, None)
        self.assertRaises(TypeError, operator.truediv, None, 1j)

        for denom_real, denom_imag in [(0, NAN), (NAN, 0), (NAN, NAN)]:
            z = complex(0, 0) / complex(denom_real, denom_imag)
            self.assertTrue(isnan(z.real))
            self.assertTrue(isnan(z.imag))