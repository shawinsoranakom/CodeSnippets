def test_model_choice_invalid_pk_value_error_messages(self):
        f = forms.ModelChoiceField(UUIDPK.objects.all())
        with self.assertRaisesMessage(
            ValidationError,
            "['Select a valid choice. "
            "That choice is not one of the available choices.']",
        ):
            f.clean("invalid")