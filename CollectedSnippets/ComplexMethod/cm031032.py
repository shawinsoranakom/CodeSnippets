def test_fromkindanddata(self):
        """Test PyUnicode_FromKindAndData()"""
        from _testcapi import unicode_fromkindanddata as fromkindanddata

        strings = [
            'abcde', '\xa1\xa2\xa3\xa4\xa5',
            '\u4f60\u597d\u4e16\u754c\uff01',
            '\U0001f600\U0001f601\U0001f602\U0001f603\U0001f604'
        ]
        enc1 = 'latin1'
        for s in strings[:2]:
            self.assertEqual(fromkindanddata(1, s.encode(enc1)), s)
        enc2 = 'utf-16le' if sys.byteorder == 'little' else 'utf-16be'
        for s in strings[:3]:
            self.assertEqual(fromkindanddata(2, s.encode(enc2)), s)
        enc4 = 'utf-32le' if sys.byteorder == 'little' else 'utf-32be'
        for s in strings:
            self.assertEqual(fromkindanddata(4, s.encode(enc4)), s)
        self.assertEqual(fromkindanddata(2, '\U0001f600'.encode(enc2)),
                         '\ud83d\ude00')
        for kind in 1, 2, 4:
            self.assertEqual(fromkindanddata(kind, b''), '')
            self.assertEqual(fromkindanddata(kind, b'\0'*kind), '\0')
            self.assertEqual(fromkindanddata(kind, NULL, 0), '')

        for kind in -1, 0, 3, 5, 8:
            self.assertRaises(SystemError, fromkindanddata, kind, b'')
        self.assertRaises(ValueError, fromkindanddata, 1, b'abc', -1)
        self.assertRaises(ValueError, fromkindanddata, 1, b'abc', PY_SSIZE_T_MIN)
        self.assertRaises(ValueError, fromkindanddata, 1, NULL, -1)
        self.assertRaises(ValueError, fromkindanddata, 1, NULL, PY_SSIZE_T_MIN)