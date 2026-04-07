def test_model_multiple_choice_null_characters(self):
        f = forms.ModelMultipleChoiceField(queryset=ExplicitPK.objects.all())
        msg = "Null characters are not allowed."
        with self.assertRaisesMessage(ValidationError, msg):
            f.clean(["\x00something"])

        with self.assertRaisesMessage(ValidationError, msg):
            f.clean(["valid", "\x00something"])