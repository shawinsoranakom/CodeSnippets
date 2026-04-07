def test_label_suffix_override(self):
        """
        BoundField label_suffix (if provided) overrides Form label_suffix
        """

        class SomeForm(Form):
            field = CharField()

        boundfield = SomeForm(label_suffix="!")["field"]

        self.assertHTMLEqual(
            boundfield.label_tag(label_suffix="$"),
            '<label for="id_field">Field$</label>',
        )
        self.assertHTMLEqual(
            boundfield.legend_tag(label_suffix="$"),
            "<legend>Field$</legend>",
        )