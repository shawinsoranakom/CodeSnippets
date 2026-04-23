def test_non_relational_field_nested(self):
        with self.assertRaisesMessage(
            FieldError, self.non_relational_error % ("name", "family")
        ):
            list(Species.objects.select_related("genus__name"))