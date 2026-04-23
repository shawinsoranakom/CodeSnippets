def test_constructor(self):
        r = self.BytesIO(b"\xc3\xa9\n\n")
        b = self.BufferedReader(r, 1000)
        t = self.TextIOWrapper(b, encoding="utf-8")
        t.__init__(b, encoding="latin-1", newline="\r\n")
        self.assertEqual(t.encoding, "latin-1")
        self.assertEqual(t.line_buffering, False)
        t.__init__(b, encoding="utf-8", line_buffering=True)
        self.assertEqual(t.encoding, "utf-8")
        self.assertEqual(t.line_buffering, True)
        self.assertEqual("\xe9\n", t.readline())
        invalid_type = TypeError if self.is_C else ValueError
        with self.assertRaises(invalid_type):
            t.__init__(b, encoding=42)
        with self.assertRaises(UnicodeEncodeError):
            t.__init__(b, encoding='\udcfe')
        with self.assertRaises(ValueError):
            t.__init__(b, encoding='utf-8\0')
        with self.assertRaises(invalid_type):
            t.__init__(b, encoding="utf-8", errors=42)
        if support.Py_DEBUG or sys.flags.dev_mode or self.is_C:
            with self.assertRaises(UnicodeEncodeError):
                t.__init__(b, encoding="utf-8", errors='\udcfe')
        if support.Py_DEBUG or sys.flags.dev_mode or self.is_C:
            with self.assertRaises(ValueError):
                t.__init__(b, encoding="utf-8", errors='replace\0')
        with self.assertRaises(TypeError):
            t.__init__(b, encoding="utf-8", newline=42)
        with self.assertRaises(ValueError):
            t.__init__(b, encoding="utf-8", newline='\udcfe')
        with self.assertRaises(ValueError):
            t.__init__(b, encoding="utf-8", newline='\n\0')
        with self.assertRaises(ValueError):
            t.__init__(b, encoding="utf-8", newline='xyzzy')