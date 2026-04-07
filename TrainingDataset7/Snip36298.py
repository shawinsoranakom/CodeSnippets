def test_smart_bytes(self):
        class Test:
            def __str__(self):
                return "ŠĐĆŽćžšđ"

        lazy_func = gettext_lazy("x")
        self.assertIs(smart_bytes(lazy_func), lazy_func)
        self.assertEqual(
            smart_bytes(Test()),
            b"\xc5\xa0\xc4\x90\xc4\x86\xc5\xbd\xc4\x87\xc5\xbe\xc5\xa1\xc4\x91",
        )
        self.assertEqual(smart_bytes(1), b"1")
        self.assertEqual(smart_bytes("foo"), b"foo")