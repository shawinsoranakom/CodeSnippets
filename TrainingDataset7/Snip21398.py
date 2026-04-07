def test_incorrect_field_in_F_expression(self):
        with self.assertRaisesMessage(
            FieldError, "Cannot resolve keyword 'nope' into field."
        ):
            list(Employee.objects.filter(firstname=F("nope")))