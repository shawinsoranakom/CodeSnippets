def test_strip_tags(self):
        # Python fixed a quadratic-time issue in HTMLParser in 3.13.6, 3.12.12.
        # The fix slightly changes HTMLParser's output, so tests for
        # particularly malformed input must handle both old and new results.
        # The check below is temporary until all supported Python versions and
        # CI workers include the fix. See:
        # https://github.com/python/cpython/commit/6eb6c5db
        min_fixed_security = {
            (3, 13): (3, 13, 6),
            (3, 12): (3, 12, 12),
        }
        # Similarly, there was a fix for terminating incomplete entities. See:
        # https://github.com/python/cpython/commit/95296a9d
        min_fixed_incomplete_entities = {
            (3, 14): (3, 14, 1),
            (3, 13): (3, 13, 10),
            (3, 12): (3, 12, math.inf),  # not fixed in 3.12.
        }
        major_version = sys.version_info[:2]
        htmlparser_fixed_security = sys.version_info >= min_fixed_security.get(
            major_version, major_version
        )
        htmlparser_fixed_incomplete_entities = (
            sys.version_info
            >= min_fixed_incomplete_entities.get(major_version, major_version)
        )
        items = (
            (
                "<p>See: &#39;&eacute; is an apostrophe followed by e acute</p>",
                "See: &#39;&eacute; is an apostrophe followed by e acute",
            ),
            (
                "<p>See: &#x27;&eacute; is an apostrophe followed by e acute</p>",
                "See: &#x27;&eacute; is an apostrophe followed by e acute",
            ),
            ("<adf>a", "a"),
            ("</adf>a", "a"),
            ("<asdf><asdf>e", "e"),
            ("hi, <f x", "hi, <f x"),
            ("234<235, right?", "234<235, right?"),
            ("a4<a5 right?", "a4<a5 right?"),
            ("b7>b2!", "b7>b2!"),
            ("</fe", "</fe"),
            ("<x>b<y>", "b"),
            ("a<p onclick=\"alert('<test>')\">b</p>c", "abc"),
            ("a<p a >b</p>c", "abc"),
            ("d<a:b c:d>e</p>f", "def"),
            ('<strong>foo</strong><a href="http://example.com">bar</a>', "foobar"),
            # caused infinite loop on Pythons not patched with
            # https://bugs.python.org/issue20288
            ("&gotcha&#;<>", "&gotcha&#;<>"),
            ("<sc<!-- -->ript>test<<!-- -->/script>", "ript>test"),
            (
                "<script>alert()</script>&h",
                "alert()&h;" if htmlparser_fixed_incomplete_entities else "alert()h",
            ),
            (
                "><!" + ("&" * 16000) + "D",
                ">" if htmlparser_fixed_security else "><!" + ("&" * 16000) + "D",
            ),
            ("X<<<<br>br>br>br>X", "XX"),
            ("<" * 50 + "a>" * 50, ""),
            (
                ">" + "<a" * 500 + "a",
                ">" if htmlparser_fixed_security else ">" + "<a" * 500 + "a",
            ),
            ("<a" * 49 + "a" * 951, "<a" * 49 + "a" * 951),
            ("<" + "a" * 1_002, "<" + "a" * 1_002),
        )
        for value, output in items:
            with self.subTest(value=value, output=output):
                self.check_output(strip_tags, value, output)
                self.check_output(strip_tags, lazystr(value), output)