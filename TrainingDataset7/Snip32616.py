def assertChildNodeContent(self, elem, expected):
        for k, v in expected.items():
            self.assertEqual(elem.getElementsByTagName(k)[0].firstChild.wholeText, v)