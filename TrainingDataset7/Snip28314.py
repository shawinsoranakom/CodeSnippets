def test_model_multiple_choice_field_uuid_pk(self):
        f = forms.ModelMultipleChoiceField(UUIDPK.objects.all())
        with self.assertRaisesMessage(
            ValidationError, "“invalid_uuid” is not a valid value."
        ):
            f.clean(["invalid_uuid"])