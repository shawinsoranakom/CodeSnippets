def test_adds_python_format_to_all_percent_signs(self):
        self.assertMsgId(
            "1 percent sign %%, 2 percent signs %%%%, 3 percent signs %%%%%%",
            self.po_contents,
        )
        self.assertMsgId(
            "%(name)s says: 1 percent sign %%, 2 percent signs %%%%", self.po_contents
        )