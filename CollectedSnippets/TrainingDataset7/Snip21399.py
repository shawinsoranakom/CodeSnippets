def test_incorrect_joined_field_in_F_expression(self):
        with self.assertRaisesMessage(
            FieldError, "Cannot resolve keyword 'nope' into field."
        ):
            list(Company.objects.filter(ceo__pk=F("point_of_contact__nope")))