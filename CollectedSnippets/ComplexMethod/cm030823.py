def test_newobj_generic(self):
        for proto in protocols:
            for C in myclasses:
                with self.subTest(proto=proto, C=C):
                    if self.py_version < (3, 0) and proto < 2 and C in (MyInt, MyStr):
                        self.skipTest('int and str subclasses are not interoperable with Python 2')
                    if (3, 0) <= self.py_version < (3, 4) and proto < 2 and C in (MyStr, MyUnicode):
                        self.skipTest('str subclasses are not interoperable with Python < 3.4')
                    if self.py_version < (3, 15) and C == MyFrozenDict:
                        self.skipTest('frozendict is not available on Python < 3.15')
                    B = C.__base__
                    x = C(C.sample)
                    x.foo = 42
                    s = self.dumps(x, proto)
                    y = self.loads(s)
                    detail = (proto, C, B, x, y, type(y))
                    self.assert_is_copy(x, y) # XXX revisit
                    self.assertEqual(B(x), B(y), detail)
                    self.assertEqual(x.__dict__, y.__dict__, detail)