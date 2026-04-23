def test_invalid_field(self):
        with self.assertRaisesMessage(
            FieldError, self.invalid_error % ("invalid_field", "genus")
        ):
            list(Species.objects.select_related("invalid_field"))

        with self.assertRaisesMessage(
            FieldError, self.invalid_error % ("related_invalid_field", "family")
        ):
            list(Species.objects.select_related("genus__related_invalid_field"))

        with self.assertRaisesMessage(
            FieldError, self.invalid_error % ("invalid_field", "(none)")
        ):
            list(Domain.objects.select_related("invalid_field"))