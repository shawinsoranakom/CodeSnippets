def test_model_field_that_returns_none_to_exclude_itself_with_explicit_fields(self):
        self.assertEqual(list(CustomFieldForExclusionForm.base_fields), ["name"])
        self.assertHTMLEqual(
            str(CustomFieldForExclusionForm()),
            '<div><label for="id_name">Name:</label><input type="text" '
            'name="name" maxlength="10" required id="id_name"></div>',
        )