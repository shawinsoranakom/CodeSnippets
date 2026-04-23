def test_sum(self):
        self.assertEqual(sum([]), 0)
        self.assertEqual(sum(list(range(2,8))), 27)
        self.assertEqual(sum(iter(list(range(2,8)))), 27)
        self.assertEqual(sum(Squares(10)), 285)
        self.assertEqual(sum(iter(Squares(10))), 285)
        self.assertEqual(sum([[1], [2], [3]], []), [1, 2, 3])

        self.assertEqual(sum(range(10), 1000), 1045)
        self.assertEqual(sum(range(10), start=1000), 1045)
        self.assertEqual(sum(range(10), 2**31-5), 2**31+40)
        self.assertEqual(sum(range(10), 2**63-5), 2**63+40)

        self.assertEqual(sum(i % 2 != 0 for i in range(10)), 5)
        self.assertEqual(sum((i % 2 != 0 for i in range(10)), 2**31-3),
                         2**31+2)
        self.assertEqual(sum((i % 2 != 0 for i in range(10)), 2**63-3),
                         2**63+2)
        self.assertIs(sum([], False), False)

        self.assertEqual(sum(i / 2 for i in range(10)), 22.5)
        self.assertEqual(sum((i / 2 for i in range(10)), 1000), 1022.5)
        self.assertEqual(sum((i / 2 for i in range(10)), 1000.25), 1022.75)
        self.assertEqual(sum([0.5, 1]), 1.5)
        self.assertEqual(sum([1, 0.5]), 1.5)
        self.assertEqual(repr(sum([-0.0])), '0.0')
        self.assertEqual(repr(sum([-0.0], -0.0)), '-0.0')
        self.assertEqual(repr(sum([], -0.0)), '-0.0')
        self.assertTrue(math.isinf(sum([float("inf"), float("inf")])))
        self.assertTrue(math.isinf(sum([1e308, 1e308])))

        self.assertRaises(TypeError, sum)
        self.assertRaises(TypeError, sum, 42)
        self.assertRaises(TypeError, sum, ['a', 'b', 'c'])
        self.assertRaises(TypeError, sum, ['a', 'b', 'c'], '')
        self.assertRaises(TypeError, sum, [b'a', b'c'], b'')
        values = [bytearray(b'a'), bytearray(b'b')]
        self.assertRaises(TypeError, sum, values, bytearray(b''))
        self.assertRaises(TypeError, sum, [[1], [2], [3]])
        self.assertRaises(TypeError, sum, [{2:3}])
        self.assertRaises(TypeError, sum, [{2:3}]*2, {2:3})
        self.assertRaises(TypeError, sum, [], '')
        self.assertRaises(TypeError, sum, [], b'')
        self.assertRaises(TypeError, sum, [], bytearray())
        self.assertRaises(OverflowError, sum, [1.0, 10**1000])
        self.assertRaises(OverflowError, sum, [1j, 10**1000])

        class BadSeq:
            def __getitem__(self, index):
                raise ValueError
        self.assertRaises(ValueError, sum, BadSeq())

        empty = []
        sum(([x] for x in range(10)), empty)
        self.assertEqual(empty, [])

        xs = [complex(random.random() - .5, random.random() - .5)
              for _ in range(10000)]
        self.assertEqual(sum(xs), complex(sum(z.real for z in xs),
                                          sum(z.imag for z in xs)))

        # test that sum() of complex and real numbers doesn't
        # smash sign of imaginary 0
        self.assertComplexesAreIdentical(sum([complex(1, -0.0), 1]),
                                         complex(2, -0.0))
        self.assertComplexesAreIdentical(sum([1, complex(1, -0.0)]),
                                         complex(2, -0.0))
        self.assertComplexesAreIdentical(sum([complex(1, -0.0), 1.0]),
                                         complex(2, -0.0))
        self.assertComplexesAreIdentical(sum([1.0, complex(1, -0.0)]),
                                         complex(2, -0.0))