def test_prohibit_null_characters_validator_equality(self):
        self.assertEqual(
            ProhibitNullCharactersValidator(message="message", code="code"),
            ProhibitNullCharactersValidator(message="message", code="code"),
        )
        self.assertEqual(
            ProhibitNullCharactersValidator(), ProhibitNullCharactersValidator()
        )
        self.assertNotEqual(
            ProhibitNullCharactersValidator(message="message1", code="code"),
            ProhibitNullCharactersValidator(message="message2", code="code"),
        )
        self.assertNotEqual(
            ProhibitNullCharactersValidator(message="message", code="code1"),
            ProhibitNullCharactersValidator(message="message", code="code2"),
        )