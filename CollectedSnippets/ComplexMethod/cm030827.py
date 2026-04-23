def test_complex_newobj_ex(self):
        if self.py_version < (3, 4):
            self.skipTest('not supported in Python < 3.4')
        x = ComplexNewObjEx.__new__(ComplexNewObjEx, 0xface)  # avoid __init__
        x.abc = 666
        for proto in protocols:
            with self.subTest(proto=proto):
                if self.py_version < (3, 6) and proto < 4:
                    self.skipTest('requires protocol 4 in Python < 3.6')
                s = self.dumps(x, proto)
                if proto < 1:
                    if self.py_version >= (3, 7):
                        self.assertIn(b'\nI64206', s)  # INT
                    else:  # for test_xpickle
                        self.assertIn(b'64206', s)  # INT or LONG
                elif proto < 2:
                    self.assertIn(b'M\xce\xfa', s)  # BININT2
                elif proto < 4:
                    self.assertIn(b'X\x04\x00\x00\x00FACE', s)  # BINUNICODE
                else:
                    self.assertIn(b'\x8c\x04FACE', s)  # SHORT_BINUNICODE
                self.assertFalse(opcode_in_pickle(pickle.NEWOBJ, s))
                self.assertEqual(opcode_in_pickle(pickle.NEWOBJ_EX, s),
                                 4 <= proto)
                y = self.loads(s)   # will raise TypeError if __init__ called
                self.assert_is_copy(x, y)