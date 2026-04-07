def test_trans_tag_with_percent_symbol_in_the_middle(self):
        self.assertMsgId(
            "Literal with a percent %% symbol in the middle", self.po_contents
        )
        self.assertMsgId("It is 100%%", self.po_contents)