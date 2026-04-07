def test_python_cookies(self):
        """
        Test cases copied from Python's Lib/test/test_http_cookies.py
        """
        self.assertEqual(
            parse_cookie("chips=ahoy; vienna=finger"),
            {"chips": "ahoy", "vienna": "finger"},
        )
        # Here parse_cookie() differs from Python's cookie parsing in that it
        # treats all semicolons as delimiters, even within quotes.
        self.assertEqual(
            parse_cookie('keebler="E=mc2; L=\\"Loves\\"; fudge=\\012;"'),
            {"keebler": '"E=mc2', "L": '\\"Loves\\"', "fudge": "\\012", "": '"'},
        )
        # Illegal cookies that have an '=' char in an unquoted value.
        self.assertEqual(parse_cookie("keebler=E=mc2"), {"keebler": "E=mc2"})
        # Cookies with ':' character in their name.
        self.assertEqual(
            parse_cookie("key:term=value:term"), {"key:term": "value:term"}
        )
        # Cookies with '[' and ']'.
        self.assertEqual(
            parse_cookie("a=b; c=[; d=r; f=h"), {"a": "b", "c": "[", "d": "r", "f": "h"}
        )