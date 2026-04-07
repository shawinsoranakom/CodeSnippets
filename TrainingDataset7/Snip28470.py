def test_model_form_applies_localize_to_all_fields(self):
        class FullyLocalizedTripleForm(forms.ModelForm):
            class Meta:
                model = Triple
                localized_fields = "__all__"
                fields = "__all__"

        f = FullyLocalizedTripleForm({"left": 10, "middle": 10, "right": 10})
        self.assertTrue(f.is_valid())
        self.assertTrue(f.fields["left"].localize)
        self.assertTrue(f.fields["middle"].localize)
        self.assertTrue(f.fields["right"].localize)