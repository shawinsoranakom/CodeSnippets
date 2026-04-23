def test_realpath_invalid_paths(self):
        path = '/\x00'
        self.assertRaises(ValueError, realpath, path, strict=False)
        self.assertRaises(ValueError, realpath, path, strict=ALL_BUT_LAST)
        self.assertRaises(ValueError, realpath, path, strict=True)
        self.assertRaises(ValueError, realpath, path, strict=ALLOW_MISSING)
        path = b'/\x00'
        self.assertRaises(ValueError, realpath, path, strict=False)
        self.assertRaises(ValueError, realpath, path, strict=ALL_BUT_LAST)
        self.assertRaises(ValueError, realpath, path, strict=True)
        self.assertRaises(ValueError, realpath, path, strict=ALLOW_MISSING)
        path = '/nonexistent/x\x00'
        self.assertRaises(ValueError, realpath, path, strict=False)
        self.assertRaises(FileNotFoundError, realpath, path, strict=ALL_BUT_LAST)
        self.assertRaises(FileNotFoundError, realpath, path, strict=True)
        self.assertRaises(ValueError, realpath, path, strict=ALLOW_MISSING)
        path = b'/nonexistent/x\x00'
        self.assertRaises(ValueError, realpath, path, strict=False)
        self.assertRaises(FileNotFoundError, realpath, path, strict=ALL_BUT_LAST)
        self.assertRaises(FileNotFoundError, realpath, path, strict=True)
        self.assertRaises(ValueError, realpath, path, strict=ALLOW_MISSING)
        path = '/\x00/..'
        self.assertRaises(ValueError, realpath, path, strict=False)
        self.assertRaises(ValueError, realpath, path, strict=ALL_BUT_LAST)
        self.assertRaises(ValueError, realpath, path, strict=True)
        self.assertRaises(ValueError, realpath, path, strict=ALLOW_MISSING)
        path = b'/\x00/..'
        self.assertRaises(ValueError, realpath, path, strict=False)
        self.assertRaises(ValueError, realpath, path, strict=ALL_BUT_LAST)
        self.assertRaises(ValueError, realpath, path, strict=True)
        self.assertRaises(ValueError, realpath, path, strict=ALLOW_MISSING)

        path = '/nonexistent/x\x00/..'
        self.assertRaises(ValueError, realpath, path, strict=False)
        self.assertRaises(FileNotFoundError, realpath, path, strict=ALL_BUT_LAST)
        self.assertRaises(FileNotFoundError, realpath, path, strict=True)
        self.assertRaises(ValueError, realpath, path, strict=ALLOW_MISSING)
        path = b'/nonexistent/x\x00/..'
        self.assertRaises(ValueError, realpath, path, strict=False)
        self.assertRaises(FileNotFoundError, realpath, path, strict=ALL_BUT_LAST)
        self.assertRaises(FileNotFoundError, realpath, path, strict=True)
        self.assertRaises(ValueError, realpath, path, strict=ALLOW_MISSING)

        path = '/\udfff'
        if sys.platform == 'win32':
            self.assertEqual(realpath(path, strict=False), path)
            self.assertRaises(FileNotFoundError, realpath, path, strict=True)
            self.assertEqual(realpath(path, strict=ALLOW_MISSING), path)
        else:
            self.assertRaises(UnicodeEncodeError, realpath, path, strict=False)
            self.assertRaises(UnicodeEncodeError, realpath, path, strict=ALL_BUT_LAST)
            self.assertRaises(UnicodeEncodeError, realpath, path, strict=True)
            self.assertRaises(UnicodeEncodeError, realpath, path, strict=ALLOW_MISSING)
        path = '/nonexistent/\udfff'
        if sys.platform == 'win32':
            self.assertEqual(realpath(path, strict=False), path)
            self.assertEqual(realpath(path, strict=ALLOW_MISSING), path)
        else:
            self.assertRaises(UnicodeEncodeError, realpath, path, strict=False)
            self.assertRaises(UnicodeEncodeError, realpath, path, strict=ALLOW_MISSING)
        self.assertRaises(FileNotFoundError, realpath, path, strict=ALL_BUT_LAST)
        self.assertRaises(FileNotFoundError, realpath, path, strict=True)
        path = '/\udfff/..'
        if sys.platform == 'win32':
            self.assertEqual(realpath(path, strict=False), '/')
            self.assertRaises(FileNotFoundError, realpath, path, strict=True)
            self.assertEqual(realpath(path, strict=ALLOW_MISSING), '/')
        else:
            self.assertRaises(UnicodeEncodeError, realpath, path, strict=False)
            self.assertRaises(UnicodeEncodeError, realpath, path, strict=ALL_BUT_LAST)
            self.assertRaises(UnicodeEncodeError, realpath, path, strict=True)
            self.assertRaises(UnicodeEncodeError, realpath, path, strict=ALLOW_MISSING)
        path = '/nonexistent/\udfff/..'
        if sys.platform == 'win32':
            self.assertEqual(realpath(path, strict=False), '/nonexistent')
            self.assertEqual(realpath(path, strict=ALLOW_MISSING), '/nonexistent')
        else:
            self.assertRaises(UnicodeEncodeError, realpath, path, strict=False)
            self.assertRaises(UnicodeEncodeError, realpath, path, strict=ALLOW_MISSING)
        self.assertRaises(FileNotFoundError, realpath, path, strict=ALL_BUT_LAST)
        self.assertRaises(FileNotFoundError, realpath, path, strict=True)

        path = b'/\xff'
        if sys.platform == 'win32':
            self.assertRaises(UnicodeDecodeError, realpath, path, strict=False)
            self.assertRaises(UnicodeDecodeError, realpath, path, strict=True)
            self.assertRaises(UnicodeDecodeError, realpath, path, strict=ALLOW_MISSING)
        else:
            self.assertEqual(realpath(path, strict=False), path)
            if support.is_wasi:
                self.assertRaises(OSError, realpath, path, strict=ALL_BUT_LAST)
                self.assertRaises(OSError, realpath, path, strict=True)
                self.assertRaises(OSError, realpath, path, strict=ALLOW_MISSING)
            else:
                self.assertEqual(realpath(path, strict=ALL_BUT_LAST), path)
                self.assertRaises(FileNotFoundError, realpath, path, strict=True)
                self.assertEqual(realpath(path, strict=ALLOW_MISSING), path)
        path = b'/nonexistent/\xff'
        if sys.platform == 'win32':
            self.assertRaises(UnicodeDecodeError, realpath, path, strict=False)
            self.assertRaises(UnicodeDecodeError, realpath, path, strict=ALLOW_MISSING)
        else:
            self.assertEqual(realpath(path, strict=False), path)
        if support.is_wasi:
            self.assertRaises(OSError, realpath, path, strict=ALL_BUT_LAST)
            self.assertRaises(OSError, realpath, path, strict=True)
            self.assertRaises(OSError, realpath, path, strict=ALLOW_MISSING)
        else:
            self.assertRaises(FileNotFoundError, realpath, path, strict=ALL_BUT_LAST)
            self.assertRaises(FileNotFoundError, realpath, path, strict=True)