def test_memoryview_cast_invalid(self):
        # invalid format
        for sfmt in NON_BYTE_FORMAT:
            sformat = '@' + sfmt if randrange(2) else sfmt
            ssize = struct.calcsize(sformat)
            for dfmt in NON_BYTE_FORMAT:
                dformat = '@' + dfmt if randrange(2) else dfmt
                dsize = struct.calcsize(dformat)
                ex = ndarray(list(range(32)), shape=[32//ssize], format=sformat)
                msrc = memoryview(ex)
                self.assertRaises(TypeError, msrc.cast, dfmt, [32//dsize])

        for sfmt, sitems, _ in iter_format(1):
            ex = ndarray(sitems, shape=[1], format=sfmt)
            msrc = memoryview(ex)
            for dfmt, _, _ in iter_format(1):
                if not is_memoryview_format(dfmt):
                    self.assertRaises(ValueError, msrc.cast, dfmt,
                                      [32//dsize])
                else:
                    if not is_byte_format(sfmt) and not is_byte_format(dfmt):
                        self.assertRaises(TypeError, msrc.cast, dfmt,
                                          [32//dsize])

        # invalid shape
        size_h = struct.calcsize('h')
        size_d = struct.calcsize('d')
        ex = ndarray(list(range(2*2*size_d)), shape=[2,2,size_d], format='h')
        msrc = memoryview(ex)
        self.assertRaises(TypeError, msrc.cast, shape=[2,2,size_h], format='d')

        ex = ndarray(list(range(120)), shape=[1,2,3,4,5])
        m = memoryview(ex)

        # incorrect number of args
        self.assertRaises(TypeError, m.cast)
        self.assertRaises(TypeError, m.cast, 1, 2, 3)

        # incorrect dest format type
        self.assertRaises(TypeError, m.cast, {})

        # incorrect dest format
        self.assertRaises(ValueError, m.cast, "X")
        self.assertRaises(ValueError, m.cast, "@X")
        self.assertRaises(ValueError, m.cast, "@XY")

        # dest format not implemented
        self.assertRaises(ValueError, m.cast, "=B")
        self.assertRaises(ValueError, m.cast, "!L")
        self.assertRaises(ValueError, m.cast, "<P")
        self.assertRaises(ValueError, m.cast, ">l")
        self.assertRaises(ValueError, m.cast, "BI")
        self.assertRaises(ValueError, m.cast, "xBI")

        # src format not implemented
        ex = ndarray([(1,2), (3,4)], shape=[2], format="II")
        m = memoryview(ex)
        self.assertRaises(NotImplementedError, m.__getitem__, 0)
        self.assertRaises(NotImplementedError, m.__setitem__, 0, 8)
        self.assertRaises(NotImplementedError, m.tolist)

        # incorrect shape type
        ex = ndarray(list(range(120)), shape=[1,2,3,4,5])
        m = memoryview(ex)
        self.assertRaises(TypeError, m.cast, "B", shape={})

        # incorrect shape elements
        ex = ndarray(list(range(120)), shape=[2*3*4*5])
        m = memoryview(ex)
        self.assertRaises(OverflowError, m.cast, "B", shape=[2**64])
        self.assertRaises(ValueError, m.cast, "B", shape=[-1])
        self.assertRaises(ValueError, m.cast, "B", shape=[2,3,4,5,6,7,-1])
        self.assertRaises(ValueError, m.cast, "B", shape=[2,3,4,5,6,7,0])
        self.assertRaises(TypeError, m.cast, "B", shape=[2,3,4,5,6,7,'x'])

        # N-D -> N-D cast
        ex = ndarray(list([9 for _ in range(3*5*7*11)]), shape=[3,5,7,11])
        m = memoryview(ex)
        self.assertRaises(TypeError, m.cast, "I", shape=[2,3,4,5])

        # cast with ndim > 64
        nd = ndarray(list(range(128)), shape=[128], format='I')
        m = memoryview(nd)
        self.assertRaises(ValueError, m.cast, 'I', [1]*128)

        # view->len not a multiple of itemsize
        ex = ndarray(list([9 for _ in range(3*5*7*11)]), shape=[3*5*7*11])
        m = memoryview(ex)
        self.assertRaises(TypeError, m.cast, "I", shape=[2,3,4,5])

        # product(shape) * itemsize != buffer size
        ex = ndarray(list([9 for _ in range(3*5*7*11)]), shape=[3*5*7*11])
        m = memoryview(ex)
        self.assertRaises(TypeError, m.cast, "B", shape=[2,3,4,5])

        # product(shape) * itemsize overflow
        nd = ndarray(list(range(128)), shape=[128], format='I')
        m1 = memoryview(nd)
        nd = ndarray(list(range(128)), shape=[128], format='B')
        m2 = memoryview(nd)
        if sys.maxsize == 2**63-1:
            self.assertRaises(TypeError, m1.cast, 'B',
                              [7, 7, 73, 127, 337, 92737, 649657])
            self.assertRaises(ValueError, m1.cast, 'B',
                              [2**20, 2**20, 2**10, 2**10, 2**3])
            self.assertRaises(ValueError, m2.cast, 'I',
                              [2**20, 2**20, 2**10, 2**10, 2**1])
        else:
            self.assertRaises(TypeError, m1.cast, 'B',
                              [1, 2147483647])
            self.assertRaises(ValueError, m1.cast, 'B',
                              [2**10, 2**10, 2**5, 2**5, 2**1])
            self.assertRaises(ValueError, m2.cast, 'I',
                              [2**10, 2**10, 2**5, 2**3, 2**1])