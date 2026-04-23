def test_confused_form(self):
        class ConfusedForm(forms.ModelForm):
            """Using 'fields' *and* 'exclude'. Not sure why you'd want to do
            this, but uh, "be liberal in what you accept" and all.
            """

            class Meta:
                model = Category
                fields = ["name", "url"]
                exclude = ["url"]

        self.assertEqual(list(ConfusedForm.base_fields), ["name"])