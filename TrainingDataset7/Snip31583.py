def test_non_relational_field(self):
        with self.assertRaisesMessage(
            FieldError, self.non_relational_error % ("name", "genus")
        ):
            list(Species.objects.select_related("name__some_field"))

        with self.assertRaisesMessage(
            FieldError, self.non_relational_error % ("name", "genus")
        ):
            list(Species.objects.select_related("name"))

        with self.assertRaisesMessage(
            FieldError, self.non_relational_error % ("name", "(none)")
        ):
            list(Domain.objects.select_related("name"))