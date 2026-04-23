def test_javascript_literals(self):
        _, po_contents = self._run_makemessages(domain="djangojs")
        self.assertMsgId("This literal should be included.", po_contents)
        self.assertMsgId("gettext_noop should, too.", po_contents)
        self.assertMsgId("This one as well.", po_contents)
        self.assertMsgId(r"He said, \"hello\".", po_contents)
        self.assertMsgId("okkkk", po_contents)
        self.assertMsgId("TEXT", po_contents)
        self.assertMsgId("It's at http://example.com", po_contents)
        self.assertMsgId("String", po_contents)
        self.assertMsgId(
            "/* but this one will be too */ 'cause there is no way of telling...",
            po_contents,
        )
        self.assertMsgId("foo", po_contents)
        self.assertMsgId("bar", po_contents)
        self.assertMsgId("baz", po_contents)
        self.assertMsgId("quz", po_contents)
        self.assertMsgId("foobar", po_contents)