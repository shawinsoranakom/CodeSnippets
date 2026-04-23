def test_normalization(self):
        # Test normalize() and is_normalized()
        def check(ch, expected):
            if isinstance(expected, str):
                expected = [expected]*4
            forms = ('NFC', 'NFD', 'NFKC', 'NFKD')
            result = [self.db.normalize(form, ch) for form in forms]
            self.assertEqual(ascii(result), ascii(list(expected)))
            self.assertEqual([self.db.is_normalized(form, ch) for form in forms],
                             [ch == y for x, y in zip(result, expected)])

        check('', '')
        check('A', 'A')
        check(' ', ' ')
        check('\U0010ffff', '\U0010ffff')
        check('abc', 'abc')
        # Broken in 4.0.0
        check('\u0340', '\u0300')
        check('\u0300', '\u0300')
        check('\U0002fa1d', '\U0002a600')
        check('\U0002a600', '\U0002a600')
        check('\u0344', '\u0308\u0301')
        check('\u0308\u0301', '\u0308\u0301')
        # Broken in 4.0.0 and 4.0.1
        check('\U0001d1bc', '\U0001d1ba\U0001d165')
        check('\U0001d1ba\U0001d165', '\U0001d1ba\U0001d165')
        check('\ufb2c', '\u05e9\u05bc\u05c1')
        check('\u05e9\u05bc\u05c1', '\u05e9\u05bc\u05c1')
        check('\U0001d1c0', '\U0001d1ba\U0001d165\U0001d16f')
        check('\U0001d1ba\U0001d165\U0001d16f', '\U0001d1ba\U0001d165\U0001d16f')

        # Broken in 4.0.0
        check('\xa0', ['\xa0', '\xa0', ' ', ' '])
        check('\u2003', ['\u2003', '\u2003', ' ', ' '])
        check('\U0001d7ff', ['\U0001d7ff', '\U0001d7ff', '9', '9'])

        check('\xa8', ['\xa8', '\xa8', ' \u0308', ' \u0308'])
        check(' \u0308', ' \u0308')

        check('\xc0', ['\xc0', 'A\u0300']*2)
        check('A\u0300', ['\xc0', 'A\u0300']*2)

        check('\ud7a3', ['\ud7a3', '\u1112\u1175\u11c2']*2)
        check('\u1112\u1175\u11c2', ['\ud7a3', '\u1112\u1175\u11c2']*2)

        check('\xb4', ['\xb4', '\xb4', ' \u0301', ' \u0301'])
        check('\u1ffd', ['\xb4', '\xb4', ' \u0301', ' \u0301'])
        check(' \u0301', ' \u0301')

        check('\xc5', ['\xc5', 'A\u030a']*2)
        check('\u212b', ['\xc5', 'A\u030a']*2)
        check('A\u030a', ['\xc5', 'A\u030a']*2)

        check('\u1f71', ['\u03ac', '\u03b1\u0301']*2)
        check('\u03ac', ['\u03ac', '\u03b1\u0301']*2)
        check('\u03b1\u0301', ['\u03ac', '\u03b1\u0301']*2)

        check('\u01c4', ['\u01c4', '\u01c4', 'D\u017d', 'DZ\u030c'])
        check('D\u017d', ['D\u017d', 'DZ\u030c']*2)
        check('DZ\u030c', ['D\u017d', 'DZ\u030c']*2)

        check('\u1fed', ['\u1fed', '\xa8\u0300', ' \u0308\u0300', ' \u0308\u0300'])
        check('\xa8\u0300', ['\u1fed', '\xa8\u0300', ' \u0308\u0300', ' \u0308\u0300'])
        check(' \u0308\u0300', ' \u0308\u0300')

        check('\u326e', ['\u326e', '\u326e', '\uac00', '\u1100\u1161'])
        check('\u320e', ['\u320e', '\u320e', '(\uac00)', '(\u1100\u1161)'])
        check('(\uac00)', ['(\uac00)', '(\u1100\u1161)']*2)
        check('(\u1100\u1161)', ['(\uac00)', '(\u1100\u1161)']*2)

        check('\u0385', ['\u0385', '\xa8\u0301', ' \u0308\u0301', ' \u0308\u0301'])
        check('\u1fee', ['\u0385', '\xa8\u0301', ' \u0308\u0301', ' \u0308\u0301'])
        check('\xa8\u0301', ['\u0385', '\xa8\u0301', ' \u0308\u0301', ' \u0308\u0301'])
        check(' \u0308\u0301', ' \u0308\u0301')

        check('\u1fdf', ['\u1fdf', '\u1ffe\u0342', ' \u0314\u0342', ' \u0314\u0342'])
        check('\u1ffe\u0342', ['\u1fdf', '\u1ffe\u0342', ' \u0314\u0342', ' \u0314\u0342'])
        check('\u1ffe', ['\u1ffe', '\u1ffe', ' \u0314', ' \u0314'])
        check(' \u0314\u0342', ' \u0314\u0342')

        check('\u03d3', ['\u03d3', '\u03d2\u0301', '\u038e', '\u03a5\u0301'])
        check('\u03d2\u0301', ['\u03d3', '\u03d2\u0301', '\u038e', '\u03a5\u0301'])
        check('\u038e', ['\u038e', '\u03a5\u0301']*2)
        check('\u1feb', ['\u038e', '\u03a5\u0301']*2)
        check('\u03a5\u0301', ['\u038e', '\u03a5\u0301']*2)

        check('\u0626', ['\u0626', '\u064a\u0654']*2)
        check('\u064a\u0654', ['\u0626', '\u064a\u0654']*2)
        check('\ufe89', ['\ufe89', '\ufe89', '\u0626', '\u064a\u0654'])
        check('\ufe8a', ['\ufe8a', '\ufe8a', '\u0626', '\u064a\u0654'])
        check('\ufe8b', ['\ufe8b', '\ufe8b', '\u0626', '\u064a\u0654'])
        check('\ufe8c', ['\ufe8c', '\ufe8c', '\u0626', '\u064a\u0654'])

        check('\ufef9', ['\ufef9', '\ufef9', '\u0644\u0625', '\u0644\u0627\u0655'])
        check('\ufefa', ['\ufefa', '\ufefa', '\u0644\u0625', '\u0644\u0627\u0655'])
        check('\ufefb', ['\ufefb', '\ufefb', '\u0644\u0627', '\u0644\u0627'])
        check('\ufefc', ['\ufefc', '\ufefc', '\u0644\u0627', '\u0644\u0627'])
        check('\u0644\u0625', ['\u0644\u0625', '\u0644\u0627\u0655']*2)
        check('\u0644\u0627\u0655', ['\u0644\u0625', '\u0644\u0627\u0655']*2)
        check('\u0644\u0627', '\u0644\u0627')

        # Broken in 4.0.0
        check('\u327c', '\u327c' if self.old else
              ['\u327c', '\u327c', '\ucc38\uace0', '\u110e\u1161\u11b7\u1100\u1169'])
        check('\ucc38\uace0', ['\ucc38\uace0', '\u110e\u1161\u11b7\u1100\u1169']*2)
        check('\ucc38', ['\ucc38', '\u110e\u1161\u11b7']*2)
        check('\u110e\u1161\u11b7\u1100\u1169',
              ['\ucc38\uace0', '\u110e\u1161\u11b7\u1100\u1169']*2)
        check('\u110e\u1161\u11b7\u1100',
              ['\ucc38\u1100', '\u110e\u1161\u11b7\u1100']*2)
        check('\u110e\u1161\u11b7',
              ['\ucc38', '\u110e\u1161\u11b7']*2)
        check('\u110e\u1161',
              ['\ucc28', '\u110e\u1161']*2)
        check('\u110e', '\u110e')
        # Broken in 4.0.0-12.0.0
        check('\U00011938', '\U00011938' if self.old else
              ['\U00011938', '\U00011935\U00011930']*2)
        check('\U00011935\U00011930', ['\U00011938', '\U00011935\U00011930']*2)
        # New in 4.0.1
        check('\u321d', '\u321d' if self.old else
              ['\u321d', '\u321d', '(\uc624\uc804)', '(\u110b\u1169\u110c\u1165\u11ab)'])
        check('(\uc624\uc804)',
              ['(\uc624\uc804)', '(\u110b\u1169\u110c\u1165\u11ab)']*2)
        check('(\u110b\u1169\u110c\u1165\u11ab)',
              ['(\uc624\uc804)', '(\u110b\u1169\u110c\u1165\u11ab)']*2)
        check('\u4d57', '\u4d57')
        check('\u45d7', '\u45d7' if self.old else '\u45d7')
        check('\U0002f9bf', '\u4d57' if self.old else '\u45d7')
        # New in 4.1.0
        check('\u03a3', '\u03a3')
        check('\u03f9', '\u03f9' if self.old else
              ['\u03f9', '\u03f9', '\u03a3', '\u03a3'])
        # New in 5.0.0
        check('\u1b06', '\u1b06' if self.old else ['\u1b06', '\u1b05\u1b35']*2)
        # New in 5.2.0
        check('\U0001f213', '\U0001f213' if self.old else
                ['\U0001f213', '\U0001f213', '\u30c7', '\u30c6\u3099'])
        # New in 6.1.0
        check('\ufa2e', '\ufa2e' if self.old else '\u90de')
        # New in 13.0.0
        check('\U00011938', '\U00011938' if self.old else
                ['\U00011938', '\U00011935\U00011930', '\U00011938', '\U00011935\U00011930'])
        check('\U0001fbf9', '\U0001fbf9' if self.old else
                ['\U0001fbf9', '\U0001fbf9', '9', '9'])
        # New in 14.0.0
        check('\U000107ba', '\U000107ba' if self.old else
                ['\U000107ba', '\U000107ba', '\U0001df1e', '\U0001df1e'])
        # New in 15.0.0
        check('\U0001e06d', '\U0001e06d' if self.old else
                ['\U0001e06d', '\U0001e06d', '\u04b1', '\u04b1'])
        # New in 16.0.0
        check('\U0001ccd6', '\U0001ccd6' if self.old else
              ['\U0001ccd6', '\U0001ccd6', 'A', 'A'])

        self.assertRaises(TypeError, self.db.normalize)
        self.assertRaises(TypeError, self.db.normalize, 'NFC')
        self.assertRaises(ValueError, self.db.normalize, 'SPAM', 'A')

        self.assertRaises(TypeError, self.db.is_normalized)
        self.assertRaises(TypeError, self.db.is_normalized, 'NFC')
        self.assertRaises(ValueError, self.db.is_normalized, 'SPAM', 'A')