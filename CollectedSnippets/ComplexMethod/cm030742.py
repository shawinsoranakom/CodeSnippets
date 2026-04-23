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

        # Smith's algorithm has several sources of inaccuracy
        # for components of the result.  In examples below,
        # it's cancellation of digits in computation of sum.
        self.check_div(1e-09+1j, 1+1j)
        self.check_div(8.289760544677449e-09+0.13257307440728516j,
                       0.9059966714925808+0.5054864708672686j)

        # Just for fun.
        for i in range(100):
            x = complex(random(), random())
            y = complex(random(), random())
            self.check_div(x, y)
            y = complex(1e10*y.real, y.imag)
            self.check_div(x, y)

        self.assertAlmostEqual(complex.__truediv__(2+0j, 1+1j), 1-1j)
        self.assertRaises(TypeError, operator.truediv, 1j, None)
        self.assertRaises(TypeError, operator.truediv, None, 1j)

        for denom_real, denom_imag in [(0, NAN), (NAN, 0), (NAN, NAN)]:
            z = complex(0, 0) / complex(denom_real, denom_imag)
            self.assertTrue(isnan(z.real))
            self.assertTrue(isnan(z.imag))
            z = float(0) / complex(denom_real, denom_imag)
            self.assertTrue(isnan(z.real))
            self.assertTrue(isnan(z.imag))

        self.assertComplexesAreIdentical(complex(INF, NAN) / 2,
                                         complex(INF, NAN))

        self.assertComplexesAreIdentical(complex(INF, 1)/(0.0+1j),
                                         complex(NAN, -INF))

        # test recover of infs if numerator has infs and denominator is finite
        self.assertComplexesAreIdentical(complex(INF, -INF)/(1+0j),
                                         complex(INF, -INF))
        self.assertComplexesAreIdentical(complex(INF, INF)/(0.0+1j),
                                         complex(INF, -INF))
        self.assertComplexesAreIdentical(complex(NAN, INF)/complex(2**1000, 2**-1000),
                                         complex(INF, INF))
        self.assertComplexesAreIdentical(complex(INF, NAN)/complex(2**1000, 2**-1000),
                                         complex(INF, -INF))

        # test recover of zeros if denominator is infinite
        self.assertComplexesAreIdentical((1+1j)/complex(INF, INF), (0.0+0j))
        self.assertComplexesAreIdentical((1+1j)/complex(INF, -INF), (0.0+0j))
        self.assertComplexesAreIdentical((1+1j)/complex(-INF, INF),
                                         complex(0.0, -0.0))
        self.assertComplexesAreIdentical((1+1j)/complex(-INF, -INF),
                                         complex(-0.0, 0))
        self.assertComplexesAreIdentical((INF+1j)/complex(INF, INF),
                                         complex(NAN, NAN))
        self.assertComplexesAreIdentical(complex(1, INF)/complex(INF, INF),
                                         complex(NAN, NAN))
        self.assertComplexesAreIdentical(complex(INF, 1)/complex(1, INF),
                                         complex(NAN, NAN))

        # mixed types
        self.assertEqual((1+1j)/float(2), 0.5+0.5j)
        self.assertEqual(float(1)/(1+2j), 0.2-0.4j)
        self.assertEqual(float(1)/(-1+2j), -0.2-0.4j)
        self.assertEqual(float(1)/(1-2j), 0.2+0.4j)
        self.assertEqual(float(1)/(2+1j), 0.4-0.2j)
        self.assertEqual(float(1)/(-2+1j), -0.4-0.2j)
        self.assertEqual(float(1)/(2-1j), 0.4+0.2j)

        self.assertComplexesAreIdentical(INF/(1+0j),
                                         complex(INF, NAN))
        self.assertComplexesAreIdentical(INF/(0.0+1j),
                                         complex(NAN, -INF))
        self.assertComplexesAreIdentical(INF/complex(2**1000, 2**-1000),
                                         complex(INF, NAN))
        self.assertComplexesAreIdentical(INF/complex(NAN, NAN),
                                         complex(NAN, NAN))

        self.assertComplexesAreIdentical(float(1)/complex(INF, INF), (0.0-0j))
        self.assertComplexesAreIdentical(float(1)/complex(INF, -INF), (0.0+0j))
        self.assertComplexesAreIdentical(float(1)/complex(-INF, INF),
                                         complex(-0.0, -0.0))
        self.assertComplexesAreIdentical(float(1)/complex(-INF, -INF),
                                         complex(-0.0, 0))
        self.assertComplexesAreIdentical(float(1)/complex(INF, NAN),
                                         complex(0.0, -0.0))
        self.assertComplexesAreIdentical(float(1)/complex(-INF, NAN),
                                         complex(-0.0, -0.0))
        self.assertComplexesAreIdentical(float(1)/complex(NAN, INF),
                                         complex(0.0, -0.0))
        self.assertComplexesAreIdentical(float(INF)/complex(NAN, INF),
                                         complex(NAN, NAN))