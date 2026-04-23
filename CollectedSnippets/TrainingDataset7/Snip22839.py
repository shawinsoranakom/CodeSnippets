def test_multivalue_optional_subfields(self):
        class PhoneField(MultiValueField):
            def __init__(self, *args, **kwargs):
                fields = (
                    CharField(
                        label="Country Code",
                        validators=[
                            RegexValidator(
                                r"^\+[0-9]{1,2}$", message="Enter a valid country code."
                            )
                        ],
                    ),
                    CharField(label="Phone Number"),
                    CharField(
                        label="Extension",
                        error_messages={"incomplete": "Enter an extension."},
                    ),
                    CharField(
                        label="Label", required=False, help_text="E.g. home, work."
                    ),
                )
                super().__init__(fields, *args, **kwargs)

            def compress(self, data_list):
                if data_list:
                    return "%s.%s ext. %s (label: %s)" % tuple(data_list)
                return None

        # An empty value for any field will raise a `required` error on a
        # required `MultiValueField`.
        f = PhoneField()
        with self.assertRaisesMessage(ValidationError, "'This field is required.'"):
            f.clean("")
        with self.assertRaisesMessage(ValidationError, "'This field is required.'"):
            f.clean(None)
        with self.assertRaisesMessage(ValidationError, "'This field is required.'"):
            f.clean([])
        with self.assertRaisesMessage(ValidationError, "'This field is required.'"):
            f.clean(["+61"])
        with self.assertRaisesMessage(ValidationError, "'This field is required.'"):
            f.clean(["+61", "287654321", "123"])
        self.assertEqual(
            "+61.287654321 ext. 123 (label: Home)",
            f.clean(["+61", "287654321", "123", "Home"]),
        )
        with self.assertRaisesMessage(ValidationError, "'Enter a valid country code.'"):
            f.clean(["61", "287654321", "123", "Home"])

        # Empty values for fields will NOT raise a `required` error on an
        # optional `MultiValueField`
        f = PhoneField(required=False)
        self.assertIsNone(f.clean(""))
        self.assertIsNone(f.clean(None))
        self.assertIsNone(f.clean([]))
        self.assertEqual("+61. ext.  (label: )", f.clean(["+61"]))
        self.assertEqual(
            "+61.287654321 ext. 123 (label: )", f.clean(["+61", "287654321", "123"])
        )
        self.assertEqual(
            "+61.287654321 ext. 123 (label: Home)",
            f.clean(["+61", "287654321", "123", "Home"]),
        )
        with self.assertRaisesMessage(ValidationError, "'Enter a valid country code.'"):
            f.clean(["61", "287654321", "123", "Home"])

        # For a required `MultiValueField` with `require_all_fields=False`, a
        # `required` error will only be raised if all fields are empty. Fields
        # can individually be required or optional. An empty value for any
        # required field will raise an `incomplete` error.
        f = PhoneField(require_all_fields=False)
        with self.assertRaisesMessage(ValidationError, "'This field is required.'"):
            f.clean("")
        with self.assertRaisesMessage(ValidationError, "'This field is required.'"):
            f.clean(None)
        with self.assertRaisesMessage(ValidationError, "'This field is required.'"):
            f.clean([])
        with self.assertRaisesMessage(ValidationError, "'Enter a complete value.'"):
            f.clean(["+61"])
        self.assertEqual(
            "+61.287654321 ext. 123 (label: )", f.clean(["+61", "287654321", "123"])
        )
        with self.assertRaisesMessage(
            ValidationError, "'Enter a complete value.', 'Enter an extension.'"
        ):
            f.clean(["", "", "", "Home"])
        with self.assertRaisesMessage(ValidationError, "'Enter a valid country code.'"):
            f.clean(["61", "287654321", "123", "Home"])

        # For an optional `MultiValueField` with `require_all_fields=False`, we
        # don't get any `required` error but we still get `incomplete` errors.
        f = PhoneField(required=False, require_all_fields=False)
        self.assertIsNone(f.clean(""))
        self.assertIsNone(f.clean(None))
        self.assertIsNone(f.clean([]))
        with self.assertRaisesMessage(ValidationError, "'Enter a complete value.'"):
            f.clean(["+61"])
        self.assertEqual(
            "+61.287654321 ext. 123 (label: )", f.clean(["+61", "287654321", "123"])
        )
        with self.assertRaisesMessage(
            ValidationError, "'Enter a complete value.', 'Enter an extension.'"
        ):
            f.clean(["", "", "", "Home"])
        with self.assertRaisesMessage(ValidationError, "'Enter a valid country code.'"):
            f.clean(["61", "287654321", "123", "Home"])