def test_folding_white_space(self):
        """
        Test for correct use of "folding white space" in long headers (#7747)
        """
        email = EmailMessage(
            "Long subject lines that get wrapped should contain a space continuation "
            "character to comply with RFC 822",
        )
        message = email.message()
        msg_bytes = message.as_bytes()
        self.assertIn(
            b"Subject: Long subject lines that get wrapped should contain a space\n"
            b" continuation character to comply with RFC 822",
            msg_bytes,
        )