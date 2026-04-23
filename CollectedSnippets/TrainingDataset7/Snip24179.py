def assertChildNodes(self, elem, expected):
        "Taken from syndication/tests.py."
        actual = {n.nodeName for n in elem.childNodes}
        expected = set(expected)
        self.assertEqual(actual, expected)