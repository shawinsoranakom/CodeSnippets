def test_fromkeys_with_nondefault_encoding(self):
        key_utf16 = b"\xff\xfe\x8e\x02\xdd\x01\x9e\x02"
        value_utf16 = b"\xff\xfe\xdd\x01n\x00l\x00P\x02\x8c\x02"
        q = QueryDict.fromkeys([key_utf16], value=value_utf16, encoding="utf-16")
        expected = QueryDict("", mutable=True)
        expected["ʎǝʞ"] = "ǝnlɐʌ"
        self.assertEqual(q, expected)