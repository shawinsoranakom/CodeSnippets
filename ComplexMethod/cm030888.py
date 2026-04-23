def test_passing_values(self):
        passValue = self.passValue

        self.assertEqual(passValue(True), True if self.wantobjects else '1')
        self.assertEqual(passValue(False), False if self.wantobjects else '0')
        self.assertEqual(passValue('string'), 'string')
        self.assertEqual(passValue('string\u20ac'), 'string\u20ac')
        self.assertEqual(passValue('string\U0001f4bb'), 'string\U0001f4bb')
        self.assertEqual(passValue('str\x00ing'), 'str\x00ing')
        self.assertEqual(passValue('str\x00ing\xbd'), 'str\x00ing\xbd')
        self.assertEqual(passValue('str\x00ing\u20ac'), 'str\x00ing\u20ac')
        self.assertEqual(passValue('str\x00ing\U0001f4bb'),
                         'str\x00ing\U0001f4bb')
        if sys.platform != 'win32':
            self.assertEqual(passValue('<\udce2\udc82\udcac>'),
                             '<\u20ac>')
            self.assertEqual(passValue('<\udced\udca0\udcbd\udced\udcb2\udcbb>'),
                             '<\U0001f4bb>')
        self.assertEqual(passValue(b'str\x00ing'),
                         b'str\x00ing' if self.wantobjects else 'str\x00ing')
        self.assertEqual(passValue(b'str\xc0\x80ing'),
                         b'str\xc0\x80ing' if self.wantobjects else 'str\xc0\x80ing')
        self.assertEqual(passValue(b'str\xbding'),
                         b'str\xbding' if self.wantobjects else 'str\xbding')
        for i in self.get_integers():
            self.assertEqual(passValue(i), i if self.wantobjects else str(i))
        for f in (0.0, 1.0, -1.0, 1/3,
                  sys.float_info.min, sys.float_info.max,
                  -sys.float_info.min, -sys.float_info.max):
            if self.wantobjects:
                self.assertEqual(passValue(f), f)
            else:
                self.assertEqual(float(passValue(f)), f)
        if self.wantobjects:
            f = passValue(float('nan'))
            self.assertNotEqual(f, f)
            self.assertEqual(passValue(float('inf')), float('inf'))
            self.assertEqual(passValue(-float('inf')), -float('inf'))
        else:
            self.assertEqual(float(passValue(float('inf'))), float('inf'))
            self.assertEqual(float(passValue(-float('inf'))), -float('inf'))
            # XXX NaN representation can be not parsable by float()
        self.assertEqual(passValue((1, '2', (3.4,))),
                         (1, '2', (3.4,)) if self.wantobjects else '1 2 3.4')
        self.assertEqual(passValue(['a', ['b', 'c']]),
                         ('a', ('b', 'c')) if self.wantobjects else 'a {b c}')