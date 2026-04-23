def test_newobj_proxies(self):
        # NEWOBJ should use the __class__ rather than the raw type
        classes = myclasses[:]
        # Cannot create weakproxies to these classes
        for c in (MyInt, MyLong, MyTuple):
            classes.remove(c)
        for proto in protocols:
            for C in classes:
                with self.subTest(proto=proto, C=C):
                    if self.py_version < (3, 4) and proto < 3 and C in (MyStr, MyUnicode):
                        self.skipTest('str subclasses are not interoperable with Python < 3.4')
                    if self.py_version < (3, 15) and C == MyFrozenDict:
                        self.skipTest('frozendict is not available on Python < 3.15')
                    B = C.__base__
                    x = C(C.sample)
                    x.foo = 42
                    p = weakref.proxy(x)
                    s = self.dumps(p, proto)
                    y = self.loads(s)
                    self.assertEqual(type(y), type(x))  # rather than type(p)
                    detail = (proto, C, B, x, y, type(y))
                    self.assertEqual(B(x), B(y), detail)
                    self.assertEqual(x.__dict__, y.__dict__, detail)