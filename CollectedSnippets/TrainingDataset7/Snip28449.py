def test_form_subclass_inheritance(self):
        class Form(forms.Form):
            age = forms.IntegerField()

        class ModelForm(forms.ModelForm, Form):
            class Meta:
                model = Writer
                fields = "__all__"

        self.assertEqual(list(ModelForm().fields), ["name", "age"])