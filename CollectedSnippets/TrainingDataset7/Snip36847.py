def test_domain_name_equality(self):
        self.assertEqual(
            DomainNameValidator(),
            DomainNameValidator(),
        )
        self.assertNotEqual(
            DomainNameValidator(),
            EmailValidator(),
        )
        self.assertNotEqual(
            DomainNameValidator(),
            DomainNameValidator(code="custom_code"),
        )
        self.assertEqual(
            DomainNameValidator(message="custom error message"),
            DomainNameValidator(message="custom error message"),
        )
        self.assertNotEqual(
            DomainNameValidator(message="custom error message"),
            DomainNameValidator(message="custom error message", code="custom_code"),
        )