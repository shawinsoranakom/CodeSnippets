def test_unequal_html(self):
        self.assertHTMLNotEqual("<p>Hello</p>", "<p>Hello!</p>")
        self.assertHTMLNotEqual("<p>foo&#20;bar</p>", "<p>foo&nbsp;bar</p>")
        self.assertHTMLNotEqual("<p>foo bar</p>", "<p>foo &nbsp;bar</p>")
        self.assertHTMLNotEqual("<p>foo nbsp</p>", "<p>foo &nbsp;</p>")
        self.assertHTMLNotEqual("<p>foo #20</p>", "<p>foo &#20;</p>")
        self.assertHTMLNotEqual(
            "<p><span>Hello</span><span>World</span></p>",
            "<p><span>Hello</span>World</p>",
        )
        self.assertHTMLNotEqual(
            "<p><span>Hello</span>World</p>",
            "<p><span>Hello</span><span>World</span></p>",
        )