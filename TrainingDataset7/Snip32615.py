def assertChildNodes(self, elem, expected):
        actual = {n.nodeName for n in elem.childNodes}
        expected = set(expected)
        self.assertEqual(actual, expected)