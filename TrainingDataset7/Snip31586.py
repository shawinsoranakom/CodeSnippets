def test_reverse_relational_field(self):
        with self.assertRaisesMessage(
            FieldError, self.invalid_error % ("child_1", "genus")
        ):
            list(Species.objects.select_related("child_1"))