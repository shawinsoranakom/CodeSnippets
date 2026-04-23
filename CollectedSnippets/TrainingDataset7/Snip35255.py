def test_class_attribute(self):
        pairs = [
            ('<p class="foo bar"></p>', '<p class="bar foo"></p>'),
            ('<p class=" foo bar "></p>', '<p class="bar foo"></p>'),
            ('<p class="   foo    bar    "></p>', '<p class="bar foo"></p>'),
            ('<p class="foo\tbar"></p>', '<p class="bar foo"></p>'),
            ('<p class="\tfoo\tbar\t"></p>', '<p class="bar foo"></p>'),
            ('<p class="\t\t\tfoo\t\t\tbar\t\t\t"></p>', '<p class="bar foo"></p>'),
            ('<p class="\t \nfoo \t\nbar\n\t "></p>', '<p class="bar foo"></p>'),
        ]
        for html1, html2 in pairs:
            with self.subTest(html1):
                self.assertHTMLEqual(html1, html2)