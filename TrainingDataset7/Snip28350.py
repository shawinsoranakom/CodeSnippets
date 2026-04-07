def test_orderfields_form(self):
        class OrderFields(forms.ModelForm):
            class Meta:
                model = Category
                fields = ["url", "name"]

        self.assertEqual(list(OrderFields.base_fields), ["url", "name"])
        self.assertHTMLEqual(
            str(OrderFields()),
            '<div><label for="id_url">The URL:</label>'
            '<input type="text" name="url" maxlength="40" required id="id_url">'
            '</div><div><label for="id_name">Name:</label><input type="text" '
            'name="name" maxlength="20" required id="id_name"></div>',
        )