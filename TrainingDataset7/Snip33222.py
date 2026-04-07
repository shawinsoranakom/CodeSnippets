def test_invalid_email(self):
        """
        #17592 - Check urlize don't crash on invalid email with dot-starting
        domain
        """
        self.assertEqual(urlize("email@.stream.ru"), "email@.stream.ru")