def test_fill(self):
        """Test PyUnicode_Fill()"""
        from _testcapi import unicode_fill as fill

        strings = [
            # all strings have exactly 5 characters
            'abcde', '\xa1\xa2\xa3\xa4\xa5',
            '\u4f60\u597d\u4e16\u754c\uff01',
            '\U0001f600\U0001f601\U0001f602\U0001f603\U0001f604'
        ]
        chars = [0x78, 0xa9, 0x20ac, 0x1f638]

        for idx, fill_char in enumerate(chars):
            # wide -> narrow: exceed maxchar limitation
            for to in strings[:idx]:
                self.assertRaises(ValueError, fill, to, 0, 0, fill_char)
            for to in strings[idx:]:
                for start in [*range(7), PY_SSIZE_T_MAX]:
                    for length in [*range(-1, 7 - start), PY_SSIZE_T_MIN, PY_SSIZE_T_MAX]:
                        filled = max(min(length, 5 - start), 0)
                        if filled == 5 and to != strings[idx]:
                            # narrow -> wide
                            # Tests omitted since this creates invalid strings.
                            continue
                        expected = to[:start] + chr(fill_char) * filled + to[start + filled:]
                        self.assertEqual(fill(to, start, length, fill_char),
                                        (expected, filled))

        s = strings[0]
        self.assertRaises(IndexError, fill, s, -1, 0, 0x78)
        self.assertRaises(IndexError, fill, s, PY_SSIZE_T_MIN, 0, 0x78)
        self.assertRaises(ValueError, fill, s, 0, 0, 0x110000)
        self.assertRaises(SystemError, fill, b'abc', 0, 0, 0x78)
        self.assertRaises(SystemError, fill, [], 0, 0, 0x78)