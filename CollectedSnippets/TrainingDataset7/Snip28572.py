def test_modelformset_factory_widgets(self):
        widgets = {"name": forms.TextInput(attrs={"class": "poet"})}
        PoetFormSet = modelformset_factory(Poet, fields="__all__", widgets=widgets)
        form = PoetFormSet.form()
        self.assertHTMLEqual(
            str(form["name"]),
            '<input id="id_name" maxlength="100" type="text" class="poet" name="name" '
            "required>",
        )