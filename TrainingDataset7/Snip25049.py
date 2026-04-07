def test_trans_tag_with_string_that_look_like_fmt_spec(self):
        self.assertMsgId(
            "Looks like a str fmt spec %%s but should not be interpreted as such",
            self.po_contents,
        )
        self.assertMsgId(
            "Looks like a str fmt spec %% o but should not be interpreted as such",
            self.po_contents,
        )