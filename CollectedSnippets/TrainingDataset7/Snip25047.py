def test_trans_tag_with_percent_symbol_at_the_end(self):
        self.assertMsgId(
            "Literal with a percent symbol at the end %%", self.po_contents
        )