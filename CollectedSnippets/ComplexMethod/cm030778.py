def test_memoryview_assign(self):

        # ndim = 0
        ex = ndarray(12.5, shape=[], format='f', flags=ND_WRITABLE)
        m = memoryview(ex)
        m[()] = 22.5
        self.assertEqual(m[()], 22.5)
        m[...] = 23.5
        self.assertEqual(m[()], 23.5)
        self.assertRaises(TypeError, m.__setitem__, 0, 24.7)

        # read-only
        ex = ndarray(list(range(7)), shape=[7])
        m = memoryview(ex)
        self.assertRaises(TypeError, m.__setitem__, 2, 10)

        # range
        ex = ndarray(list(range(7)), shape=[7], flags=ND_WRITABLE)
        m = memoryview(ex)

        self.assertRaises(IndexError, m.__setitem__, 2**64, 9)
        self.assertRaises(TypeError, m.__setitem__, 2.0, 10)
        self.assertRaises(TypeError, m.__setitem__, 0.0, 11)

        # out of bounds
        self.assertRaises(IndexError, m.__setitem__, -8, 20)
        self.assertRaises(IndexError, m.__setitem__, 8, 25)

        # pack_single() success:
        for fmt in fmtdict['@']:
            if fmt == 'c' or fmt == '?':
                continue
            ex = ndarray([1,2,3], shape=[3], format=fmt, flags=ND_WRITABLE)
            m = memoryview(ex)
            i = randrange(-3, 3)
            m[i] = 8
            self.assertEqual(m[i], 8)
            self.assertEqual(m[i], ex[i])

        ex = ndarray([b'1', b'2', b'3'], shape=[3], format='c',
                     flags=ND_WRITABLE)
        m = memoryview(ex)
        m[2] = b'9'
        self.assertEqual(m[2], b'9')

        ex = ndarray([True, False, True], shape=[3], format='?',
                     flags=ND_WRITABLE)
        m = memoryview(ex)
        m[1] = True
        self.assertIs(m[1], True)

        # pack_single() exceptions:
        nd = ndarray([b'x'], shape=[1], format='c', flags=ND_WRITABLE)
        m = memoryview(nd)
        self.assertRaises(TypeError, m.__setitem__, 0, 100)

        ex = ndarray(list(range(144)), shape=[1,2,3,4,6], flags=ND_WRITABLE)
        m1 = memoryview(ex)

        for fmt, _range in fmtdict['@'].items():
            if (fmt == '?'): # PyObject_IsTrue() accepts anything
                continue
            if fmt == 'c': # special case tested above
                continue
            m2 = m1.cast(fmt)
            lo, hi = _range
            if fmt in "dfDF":
                lo, hi = -2**1024, 2**1024
            if fmt != 'P': # PyLong_AsVoidPtr() accepts negative numbers
                self.assertRaises(ValueError, m2.__setitem__, 0, lo-1)
                self.assertRaises(TypeError, m2.__setitem__, 0, "xyz")
            self.assertRaises(ValueError, m2.__setitem__, 0, hi)

        # invalid item
        m2 = m1.cast('c')
        self.assertRaises(ValueError, m2.__setitem__, 0, b'\xff\xff')

        # format not implemented
        ex = ndarray(list(range(1)), shape=[1], format="xL", flags=ND_WRITABLE)
        m = memoryview(ex)
        self.assertRaises(NotImplementedError, m.__setitem__, 0, 1)

        ex = ndarray([b'12345'], shape=[1], format="s", flags=ND_WRITABLE)
        m = memoryview(ex)
        self.assertRaises(NotImplementedError, m.__setitem__, 0, 1)

        # multi-dimensional
        ex = ndarray(list(range(12)), shape=[3,4], flags=ND_WRITABLE)
        m = memoryview(ex)
        m[0,1] = 42
        self.assertEqual(ex[0][1], 42)
        m[-1,-1] = 43
        self.assertEqual(ex[2][3], 43)
        # errors
        for index in (3, -4):
            with self.assert_out_of_bounds_error(dim=1):
                m[index, 0] = 0
        for index in (4, -5):
            with self.assert_out_of_bounds_error(dim=2):
                m[0, index] = 0
        self.assertRaises(IndexError, m.__setitem__, (2**64, 0), 0)
        self.assertRaises(IndexError, m.__setitem__, (0, 2**64), 0)

        self.assertRaises(TypeError, m.__setitem__, (0, 0, 0), 0)
        self.assertRaises(TypeError, m.__setitem__, (0.0, 0.0), 0)

        # Not implemented: multidimensional sub-views
        self.assertRaises(NotImplementedError, m.__setitem__, 0, [2, 3])