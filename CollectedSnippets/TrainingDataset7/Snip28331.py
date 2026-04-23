def test_extra_declared_field_model_form(self):
        class ExtraPersonForm(forms.ModelForm):
            """ModelForm with an extra field"""

            age = forms.IntegerField()

            class Meta:
                model = Person
                fields = ("name", "age")