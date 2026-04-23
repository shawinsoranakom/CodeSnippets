def test_long(self):
        # Check conversions from string
        LL = [
                ('1' + '0'*20, 10**20),
                ('1' + '0'*100, 10**100)
        ]
        for s, v in LL:
            for sign in "", "+", "-":
                for prefix in "", " ", "\t", "  \t\t  ":
                    ss = prefix + sign + s
                    vv = v
                    if sign == "-" and v is not ValueError:
                        vv = -v
                    try:
                        self.assertEqual(int(ss), vv)
                    except ValueError:
                        pass

        # trailing L should no longer be accepted...
        self.assertRaises(ValueError, int, '123L')
        self.assertRaises(ValueError, int, '123l')
        self.assertRaises(ValueError, int, '0L')
        self.assertRaises(ValueError, int, '-37L')
        self.assertRaises(ValueError, int, '0x32L', 16)
        self.assertRaises(ValueError, int, '1L', 21)
        # ... but it's just a normal digit if base >= 22
        self.assertEqual(int('1L', 22), 43)

        # tests with base 0
        self.assertEqual(int('000', 0), 0)
        self.assertEqual(int('0o123', 0), 83)
        self.assertEqual(int('0x123', 0), 291)
        self.assertEqual(int('0b100', 0), 4)
        self.assertEqual(int(' 0O123   ', 0), 83)
        self.assertEqual(int(' 0X123  ', 0), 291)
        self.assertEqual(int(' 0B100 ', 0), 4)
        self.assertEqual(int('0', 0), 0)
        self.assertEqual(int('+0', 0), 0)
        self.assertEqual(int('-0', 0), 0)
        self.assertEqual(int('00', 0), 0)
        self.assertRaises(ValueError, int, '08', 0)
        self.assertRaises(ValueError, int, '-012395', 0)

        # invalid bases
        invalid_bases = [-909,
                          2**31-1, 2**31, -2**31, -2**31-1,
                          2**63-1, 2**63, -2**63, -2**63-1,
                          2**100, -2**100,
                          ]
        for base in invalid_bases:
            self.assertRaises(ValueError, int, '42', base)

        # Invalid unicode string
        # See bpo-34087
        self.assertRaises(ValueError, int, '\u3053\u3093\u306b\u3061\u306f')