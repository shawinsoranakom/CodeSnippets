def test_subclassmeta_form(self):
        class SomeCategoryForm(forms.ModelForm):
            checkbox = forms.BooleanField()

            class Meta:
                model = Category
                fields = "__all__"

        class SubclassMeta(SomeCategoryForm):
            """We can also subclass the Meta inner class to change the fields
            list.
            """

            class Meta(SomeCategoryForm.Meta):
                exclude = ["url"]

        self.assertHTMLEqual(
            str(SubclassMeta()),
            '<div><label for="id_name">Name:</label>'
            '<input type="text" name="name" maxlength="20" required id="id_name">'
            '</div><div><label for="id_slug">Slug:</label><input type="text" '
            'name="slug" maxlength="20" required id="id_slug"></div><div>'
            '<label for="id_checkbox">Checkbox:</label>'
            '<input type="checkbox" name="checkbox" required id="id_checkbox"></div>',
        )