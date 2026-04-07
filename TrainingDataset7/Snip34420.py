def test_token_smart_split(self):
        """
        #7027 -- _() syntax should work with spaces
        """
        token = Token(
            TokenType.BLOCK, 'sometag _("Page not found") value|yesno:_("yes,no")'
        )
        split = token.split_contents()
        self.assertEqual(
            split, ["sometag", '_("Page not found")', 'value|yesno:_("yes,no")']
        )