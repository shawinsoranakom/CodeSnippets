def test_fromwidechar(self):
        """Test PyUnicode_FromWideChar()"""
        from _testlimitedcapi import unicode_fromwidechar as fromwidechar
        from _testcapi import SIZEOF_WCHAR_T

        if SIZEOF_WCHAR_T == 2:
            encoding = 'utf-16le' if sys.byteorder == 'little' else 'utf-16be'
        elif SIZEOF_WCHAR_T == 4:
            encoding = 'utf-32le' if sys.byteorder == 'little' else 'utf-32be'

        for s in '', 'abc', '\xa1\xa2', '\u4f60', '\U0001f600':
            b = s.encode(encoding)
            self.assertEqual(fromwidechar(b), s)
            self.assertEqual(fromwidechar(b + b'\0'*SIZEOF_WCHAR_T, -1), s)
        for s in '\ud83d', '\ude00':
            b = s.encode(encoding, 'surrogatepass')
            self.assertEqual(fromwidechar(b), s)
            self.assertEqual(fromwidechar(b + b'\0'*SIZEOF_WCHAR_T, -1), s)

        self.assertEqual(fromwidechar('abc'.encode(encoding), 2), 'ab')
        if SIZEOF_WCHAR_T == 2:
            self.assertEqual(fromwidechar('a\U0001f600'.encode(encoding), 2), 'a\ud83d')

        self.assertRaises(MemoryError, fromwidechar, b'', PY_SSIZE_T_MAX)
        self.assertRaises(SystemError, fromwidechar, b'\0'*SIZEOF_WCHAR_T, -2)
        self.assertRaises(SystemError, fromwidechar, b'\0'*SIZEOF_WCHAR_T, PY_SSIZE_T_MIN)
        self.assertEqual(fromwidechar(NULL, 0), '')
        self.assertRaises(SystemError, fromwidechar, NULL, 1)
        self.assertRaises(SystemError, fromwidechar, NULL, PY_SSIZE_T_MAX)
        self.assertRaises(SystemError, fromwidechar, NULL, -1)
        self.assertRaises(SystemError, fromwidechar, NULL, -2)
        self.assertRaises(SystemError, fromwidechar, NULL, PY_SSIZE_T_MIN)