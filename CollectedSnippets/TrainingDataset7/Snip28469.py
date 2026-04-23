def test_model_form_applies_localize_to_some_fields(self):
        class PartiallyLocalizedTripleForm(forms.ModelForm):
            class Meta:
                model = Triple
                localized_fields = (
                    "left",
                    "right",
                )
                fields = "__all__"

        f = PartiallyLocalizedTripleForm({"left": 10, "middle": 10, "right": 10})
        self.assertTrue(f.is_valid())
        self.assertTrue(f.fields["left"].localize)
        self.assertFalse(f.fields["middle"].localize)
        self.assertTrue(f.fields["right"].localize)