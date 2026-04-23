def test_serialize_class_based_validators(self):
        """
        Ticket #22943: Test serialization of class-based validators, including
        compiled regexes.
        """
        validator = RegexValidator(message="hello")
        string = MigrationWriter.serialize(validator)[0]
        self.assertEqual(
            string, "django.core.validators.RegexValidator(message='hello')"
        )
        self.serialize_round_trip(validator)

        # Test with a compiled regex.
        validator = RegexValidator(regex=re.compile(r"^\w+$"))
        string = MigrationWriter.serialize(validator)[0]
        self.assertEqual(
            string,
            "django.core.validators.RegexValidator(regex=re.compile('^\\\\w+$'))",
        )
        self.serialize_round_trip(validator)

        # Test a string regex with flag
        validator = RegexValidator(r"^[0-9]+$", flags=re.S)
        string = MigrationWriter.serialize(validator)[0]
        self.assertEqual(
            string,
            "django.core.validators.RegexValidator('^[0-9]+$', "
            "flags=re.RegexFlag['DOTALL'])",
        )
        self.serialize_round_trip(validator)

        # Test message and code
        validator = RegexValidator("^[-a-zA-Z0-9_]+$", "Invalid", "invalid")
        string = MigrationWriter.serialize(validator)[0]
        self.assertEqual(
            string,
            "django.core.validators.RegexValidator('^[-a-zA-Z0-9_]+$', 'Invalid', "
            "'invalid')",
        )
        self.serialize_round_trip(validator)

        # Test with a subclass.
        validator = EmailValidator(message="hello")
        string = MigrationWriter.serialize(validator)[0]
        self.assertEqual(
            string, "django.core.validators.EmailValidator(message='hello')"
        )
        self.serialize_round_trip(validator)

        validator = deconstructible(path="migrations.test_writer.EmailValidator")(
            EmailValidator
        )(message="hello")
        string = MigrationWriter.serialize(validator)[0]
        self.assertEqual(
            string, "migrations.test_writer.EmailValidator(message='hello')"
        )

        validator = deconstructible(path="custom.EmailValidator")(EmailValidator)(
            message="hello"
        )
        with self.assertRaisesMessage(ImportError, "No module named 'custom'"):
            MigrationWriter.serialize(validator)

        validator = deconstructible(path="django.core.validators.EmailValidator2")(
            EmailValidator
        )(message="hello")
        with self.assertRaisesMessage(
            ValueError,
            "Could not find object EmailValidator2 in django.core.validators.",
        ):
            MigrationWriter.serialize(validator)