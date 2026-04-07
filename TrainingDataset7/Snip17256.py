def test_values_wrong_alias(self):
        expected_message = (
            "Cannot resolve keyword 'alias_typo' into field. Choices are: %s"
        )
        alias_fields = ", ".join(
            sorted(["my_alias"] + list(get_field_names_from_opts(Book._meta)))
        )
        with self.assertRaisesMessage(FieldError, expected_message % alias_fields):
            Book.objects.alias(my_alias=F("pk")).order_by("alias_typo")