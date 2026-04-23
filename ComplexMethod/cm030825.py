def test_simple_newobj(self):
        x = SimpleNewObj.__new__(SimpleNewObj, 0xface)  # avoid __init__
        x.abc = 666
        for proto in protocols:
            with self.subTest(proto=proto):
                if self.py_version < (3, 0) and proto < 2:
                    self.skipTest('int subclasses are not interoperable with Python 2')
                s = self.dumps(x, proto)
                if proto < 1:
                    if self.py_version >= (3, 7):
                        self.assertIn(b'\nI64206', s)  # INT
                    else:  # for test_xpickle
                        self.assertIn(b'64206', s)  # INT or LONG
                else:
                    self.assertIn(b'M\xce\xfa', s)  # BININT2
                if not (self.py_version < (3, 5) and proto == 4):
                    self.assertEqual(opcode_in_pickle(pickle.NEWOBJ, s),
                                     2 <= proto)
                    self.assertFalse(opcode_in_pickle(pickle.NEWOBJ_EX, s))
                y = self.loads(s)   # will raise TypeError if __init__ called
                self.assert_is_copy(x, y)