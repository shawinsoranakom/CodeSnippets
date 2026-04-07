def test_model_form_refuses_arbitrary_string(self):
        msg = (
            "BrokenLocalizedTripleForm.Meta.localized_fields "
            "cannot be a string. Did you mean to type: ('foo',)?"
        )
        with self.assertRaisesMessage(TypeError, msg):

            class BrokenLocalizedTripleForm(forms.ModelForm):
                class Meta:
                    model = Triple
                    localized_fields = "foo"