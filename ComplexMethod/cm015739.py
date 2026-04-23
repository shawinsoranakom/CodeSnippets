def test_normal_integers(self):
        # Ensure the first 256 integers are shared
        a = 256
        b = 128*2
        if a is not b: self.fail('256 is not shared')
        if 12 + 24 != 36: self.fail('int op')
        if 12 + (-24) != -12: self.fail('int op')
        if (-12) + 24 != 12: self.fail('int op')
        if (-12) + (-24) != -36: self.fail('int op')
        if not 12 < 24: self.fail('int op')
        if not -24 < -12: self.fail('int op')
        # Test for a particular bug in integer multiply
        xsize, ysize, zsize = 238, 356, 4
        if not (xsize*ysize*zsize == zsize*xsize*ysize == 338912):
            self.fail('int mul commutativity')
        # And another.
        m = -sys.maxsize - 1
        for divisor in 1, 2, 4, 8, 16, 32:
            j = m // divisor
            prod = divisor * j
            if prod != m:
                self.fail("%r * %r == %r != %r" % (divisor, j, prod, m))
            if type(prod) is not int:
                self.fail("expected type(prod) to be int, not %r" %
                                   type(prod))
        # Check for unified integral type
        for divisor in 1, 2, 4, 8, 16, 32:
            j = m // divisor - 1
            prod = divisor * j
            if type(prod) is not int:
                self.fail("expected type(%r) to be int, not %r" %
                                   (prod, type(prod)))
        # Check for unified integral type
        m = sys.maxsize
        for divisor in 1, 2, 4, 8, 16, 32:
            j = m // divisor + 1
            prod = divisor * j
            if type(prod) is not int:
                self.fail("expected type(%r) to be int, not %r" %
                                   (prod, type(prod)))

        x = sys.maxsize
        self.assertIsInstance(x + 1, int,
                              "(sys.maxsize + 1) should have returned int")
        self.assertIsInstance(-x - 1, int,
                              "(-sys.maxsize - 1) should have returned int")
        self.assertIsInstance(-x - 2, int,
                              "(-sys.maxsize - 2) should have returned int")

        try: 5 << -5
        except ValueError: pass
        else: self.fail('int negative shift <<')

        try: 5 >> -5
        except ValueError: pass
        else: self.fail('int negative shift >>')