def test_foreignkeys_which_use_to_field(self):
        apple = Inventory.objects.create(barcode=86, name="Apple")
        pear = Inventory.objects.create(barcode=22, name="Pear")
        core = Inventory.objects.create(barcode=87, name="Core", parent=apple)

        field = forms.ModelChoiceField(Inventory.objects.all(), to_field_name="barcode")
        self.assertEqual(
            tuple(field.choices),
            (("", "---------"), (86, "Apple"), (87, "Core"), (22, "Pear")),
        )

        form = InventoryForm(instance=core)
        self.assertHTMLEqual(
            str(form["parent"]),
            """<select name="parent" id="id_parent">
<option value="">---------</option>
<option value="86" selected>Apple</option>
<option value="87">Core</option>
<option value="22">Pear</option>
</select>""",
        )
        data = model_to_dict(core)
        data["parent"] = "22"
        form = InventoryForm(data=data, instance=core)
        core = form.save()
        self.assertEqual(core.parent.name, "Pear")

        class CategoryForm(forms.ModelForm):
            description = forms.CharField()

            class Meta:
                model = Category
                fields = ["description", "url"]

        self.assertEqual(list(CategoryForm.base_fields), ["description", "url"])

        self.assertHTMLEqual(
            str(CategoryForm()),
            '<div><label for="id_description">Description:</label><input type="text" '
            'name="description" required id="id_description"></div><div>'
            '<label for="id_url">The URL:</label><input type="text" name="url" '
            'maxlength="40" required id="id_url"></div>',
        )
        # to_field_name should also work on ModelMultipleChoiceField.

        field = forms.ModelMultipleChoiceField(
            Inventory.objects.all(), to_field_name="barcode"
        )
        self.assertEqual(
            tuple(field.choices), ((86, "Apple"), (87, "Core"), (22, "Pear"))
        )
        self.assertSequenceEqual(field.clean([86]), [apple])

        form = SelectInventoryForm({"items": [87, 22]})
        self.assertTrue(form.is_valid())
        self.assertEqual(len(form.cleaned_data), 1)
        self.assertSequenceEqual(form.cleaned_data["items"], [core, pear])