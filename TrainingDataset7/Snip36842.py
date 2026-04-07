def test_email_equality(self):
        self.assertEqual(
            EmailValidator(),
            EmailValidator(),
        )
        self.assertNotEqual(
            EmailValidator(message="BAD EMAIL"),
            EmailValidator(),
        )
        self.assertEqual(
            EmailValidator(message="BAD EMAIL", code="bad"),
            EmailValidator(message="BAD EMAIL", code="bad"),
        )
        self.assertEqual(
            EmailValidator(allowlist=["127.0.0.1", "localhost"]),
            EmailValidator(allowlist=["localhost", "127.0.0.1"]),
        )