def test_field_removal(self):
        class ModelForm(forms.ModelForm):
            class Meta:
                model = Writer
                fields = "__all__"

        class Mixin:
            age = None

        class Form(forms.Form):
            age = forms.IntegerField()

        class Form2(forms.Form):
            foo = forms.IntegerField()

        self.assertEqual(list(ModelForm().fields), ["name"])
        self.assertEqual(list(type("NewForm", (Mixin, Form), {})().fields), [])
        self.assertEqual(
            list(type("NewForm", (Form2, Mixin, Form), {})().fields), ["foo"]
        )
        self.assertEqual(
            list(type("NewForm", (Mixin, ModelForm, Form), {})().fields), ["name"]
        )
        self.assertEqual(
            list(type("NewForm", (ModelForm, Mixin, Form), {})().fields), ["name"]
        )
        self.assertEqual(
            list(type("NewForm", (ModelForm, Form, Mixin), {})().fields),
            ["name", "age"],
        )
        self.assertEqual(
            list(type("NewForm", (ModelForm, Form), {"age": None})().fields), ["name"]
        )