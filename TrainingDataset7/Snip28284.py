def test_model_choice_null_characters(self):
        f = forms.ModelChoiceField(queryset=ExplicitPK.objects.all())
        msg = "Null characters are not allowed."
        with self.assertRaisesMessage(ValidationError, msg):
            f.clean("\x00something")