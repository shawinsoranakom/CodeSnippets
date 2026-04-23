def test_simple_equal_html(self):
        self.assertHTMLEqual("", "")
        self.assertHTMLEqual("<p></p>", "<p></p>")
        self.assertHTMLEqual("<p></p>", " <p> </p> ")
        self.assertHTMLEqual("<div><p>Hello</p></div>", "<div><p>Hello</p></div>")
        self.assertHTMLEqual("<div><p>Hello</p></div>", "<div> <p>Hello</p> </div>")
        self.assertHTMLEqual("<div>\n<p>Hello</p></div>", "<div><p>Hello</p></div>\n")
        self.assertHTMLEqual(
            "<div><p>Hello\nWorld !</p></div>", "<div><p>Hello World\n!</p></div>"
        )
        self.assertHTMLEqual(
            "<div><p>Hello\nWorld !</p></div>", "<div><p>Hello World\n!</p></div>"
        )
        self.assertHTMLEqual("<p>Hello  World   !</p>", "<p>Hello World\n\n!</p>")
        self.assertHTMLEqual("<p> </p>", "<p></p>")
        self.assertHTMLEqual("<p/>", "<p></p>")
        self.assertHTMLEqual("<p />", "<p></p>")
        self.assertHTMLEqual("<input checked>", '<input checked="checked">')
        self.assertHTMLEqual("<p>Hello", "<p> Hello")
        self.assertHTMLEqual("<p>Hello</p>World", "<p>Hello</p> World")