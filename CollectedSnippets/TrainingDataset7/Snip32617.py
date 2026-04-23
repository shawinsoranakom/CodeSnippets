def assertCategories(self, elem, expected):
        self.assertEqual(
            {
                i.firstChild.wholeText
                for i in elem.childNodes
                if i.nodeName == "category"
            },
            set(expected),
        )