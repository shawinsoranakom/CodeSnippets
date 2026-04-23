def test_name(self):
        name = self.db.name
        self.assertRaises(ValueError, name, '\0')
        self.assertRaises(ValueError, name, '\n')
        self.assertRaises(ValueError, name, '\x1F')
        self.assertRaises(ValueError, name, '\x7F')
        self.assertRaises(ValueError, name, '\x9F')
        self.assertRaises(ValueError, name, '\uFFFE')
        self.assertRaises(ValueError, name, '\uFFFF')
        self.assertRaises(ValueError, name, '\U0010FFFF')
        self.assertEqual(name('\U0010FFFF', 42), 42)

        self.assertEqual(name(' '), 'SPACE')
        self.assertEqual(name('1'), 'DIGIT ONE')
        self.assertEqual(name('A'), 'LATIN CAPITAL LETTER A')
        self.assertEqual(name('\xA0'), 'NO-BREAK SPACE')
        self.assertEqual(name('\u0221', None), None if self.old else
                         'LATIN SMALL LETTER D WITH CURL')
        self.assertEqual(name('\u3400'), 'CJK UNIFIED IDEOGRAPH-3400')
        self.assertEqual(name('\u9FA5'), 'CJK UNIFIED IDEOGRAPH-9FA5')
        self.assertEqual(name('\uAC00'), 'HANGUL SYLLABLE GA')
        self.assertEqual(name('\uD7A3'), 'HANGUL SYLLABLE HIH')
        self.assertEqual(name('\uF900'), 'CJK COMPATIBILITY IDEOGRAPH-F900')
        self.assertEqual(name('\uFA6A'), 'CJK COMPATIBILITY IDEOGRAPH-FA6A')
        self.assertEqual(name('\uFBF9'),
                         'ARABIC LIGATURE UIGHUR KIRGHIZ YEH WITH HAMZA '
                         'ABOVE WITH ALEF MAKSURA ISOLATED FORM')
        self.assertEqual(name('\U00013460', None), None if self.old else
                         'EGYPTIAN HIEROGLYPH-13460')
        self.assertEqual(name('\U000143FA', None), None if self.old else
                         'EGYPTIAN HIEROGLYPH-143FA')
        self.assertEqual(name('\U00017000', None), None if self.old else
                         'TANGUT IDEOGRAPH-17000')
        self.assertEqual(name('\U00018B00', None), None if self.old else
                         'KHITAN SMALL SCRIPT CHARACTER-18B00')
        self.assertEqual(name('\U00018CD5', None), None if self.old else
                         'KHITAN SMALL SCRIPT CHARACTER-18CD5')
        self.assertEqual(name('\U00018CFF', None), None if self.old else
                         'KHITAN SMALL SCRIPT CHARACTER-18CFF')
        self.assertEqual(name('\U00018D1E', None), None if self.old else
                         'TANGUT IDEOGRAPH-18D1E')
        self.assertEqual(name('\U0001B170', None), None if self.old else
                         'NUSHU CHARACTER-1B170')
        self.assertEqual(name('\U0001B2FB', None), None if self.old else
                         'NUSHU CHARACTER-1B2FB')
        self.assertEqual(name('\U0001FBA8', None), None if self.old else
                         'BOX DRAWINGS LIGHT DIAGONAL UPPER CENTRE TO '
                         'MIDDLE LEFT AND MIDDLE RIGHT TO LOWER CENTRE')
        self.assertEqual(name('\U0002A6D6'), 'CJK UNIFIED IDEOGRAPH-2A6D6')
        self.assertEqual(name('\U0002FA1D'), 'CJK COMPATIBILITY IDEOGRAPH-2FA1D')
        self.assertEqual(name('\U00033479', None), None if self.old else
                         'CJK UNIFIED IDEOGRAPH-33479')