def test_formfield_overrides(self):
        self.assertFormfield(
            Event,
            "start_date",
            forms.TextInput,
            formfield_overrides={DateField: {"widget": forms.TextInput}},
        )