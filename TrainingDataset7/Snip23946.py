def test_property_attribute_without_setter_defaults(self):
        with self.assertRaisesMessage(
            FieldError, "Invalid field name(s) for model Thing: 'name_in_all_caps'"
        ):
            Thing.objects.update_or_create(
                name="a", defaults={"name_in_all_caps": "FRANK"}
            )