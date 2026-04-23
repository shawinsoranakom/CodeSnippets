def test_constructor(self):
        a = Rat(10, 15)
        self.assertEqual(a.num, 2)
        self.assertEqual(a.den, 3)
        a = Rat(10, -15)
        self.assertEqual(a.num, -2)
        self.assertEqual(a.den, 3)
        a = Rat(-10, 15)
        self.assertEqual(a.num, -2)
        self.assertEqual(a.den, 3)
        a = Rat(-10, -15)
        self.assertEqual(a.num, 2)
        self.assertEqual(a.den, 3)
        a = Rat(7)
        self.assertEqual(a.num, 7)
        self.assertEqual(a.den, 1)
        try:
            a = Rat(1, 0)
        except ZeroDivisionError:
            pass
        else:
            self.fail("Rat(1, 0) didn't raise ZeroDivisionError")
        for bad in "0", 0.0, 0j, (), [], {}, None, Rat, unittest:
            try:
                a = Rat(bad)
            except TypeError:
                pass
            else:
                self.fail("Rat(%r) didn't raise TypeError" % bad)
            try:
                a = Rat(1, bad)
            except TypeError:
                pass
            else:
                self.fail("Rat(1, %r) didn't raise TypeError" % bad)