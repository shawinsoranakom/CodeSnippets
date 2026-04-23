def test_smart_split(self):
        testdata = [
            ('This is "a person" test.', ["This", "is", '"a person"', "test."]),
            ('This is "a person\'s" test.', ["This", "is", '"a person\'s"', "test."]),
            ('This is "a person\\"s" test.', ["This", "is", '"a person\\"s"', "test."]),
            ("\"a 'one", ['"a', "'one"]),
            ("all friends' tests", ["all", "friends'", "tests"]),
            (
                'url search_page words="something else"',
                ["url", "search_page", 'words="something else"'],
            ),
            (
                "url search_page words='something else'",
                ["url", "search_page", "words='something else'"],
            ),
            (
                'url search_page words "something else"',
                ["url", "search_page", "words", '"something else"'],
            ),
            (
                'url search_page words-"something else"',
                ["url", "search_page", 'words-"something else"'],
            ),
            ("url search_page words=hello", ["url", "search_page", "words=hello"]),
            (
                'url search_page words="something else',
                ["url", "search_page", 'words="something', "else"],
            ),
            ("cut:','|cut:' '", ["cut:','|cut:' '"]),
            (lazystr("a b c d"), ["a", "b", "c", "d"]),  # Test for #20231
        ]
        for test, expected in testdata:
            with self.subTest(value=test):
                self.assertEqual(list(text.smart_split(test)), expected)