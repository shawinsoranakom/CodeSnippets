def test_label(self):
        """
        ReadOnlyPasswordHashWidget doesn't contain a for attribute in the
        <label> because it doesn't have any labelable elements.
        """

        class TestForm(forms.Form):
            hash_field = ReadOnlyPasswordHashField()

        bound_field = TestForm()["hash_field"]
        self.assertIsNone(bound_field.field.widget.id_for_label("id"))
        self.assertEqual(bound_field.label_tag(), "<label>Hash field:</label>")