def test_label_has_required_css_class(self):
        """
        required_css_class is added to label_tag() and legend_tag() of required
        fields.
        """

        class SomeForm(Form):
            required_css_class = "required"
            field = CharField(max_length=10)
            field2 = IntegerField(required=False)

        f = SomeForm({"field": "test"})
        self.assertHTMLEqual(
            f["field"].label_tag(),
            '<label for="id_field" class="required">Field:</label>',
        )
        self.assertHTMLEqual(
            f["field"].legend_tag(),
            '<legend class="required">Field:</legend>',
        )
        self.assertHTMLEqual(
            f["field"].label_tag(attrs={"class": "foo"}),
            '<label for="id_field" class="foo required">Field:</label>',
        )
        self.assertHTMLEqual(
            f["field"].legend_tag(attrs={"class": "foo"}),
            '<legend class="foo required">Field:</legend>',
        )
        self.assertHTMLEqual(
            f["field2"].label_tag(), '<label for="id_field2">Field2:</label>'
        )
        self.assertHTMLEqual(
            f["field2"].legend_tag(),
            "<legend>Field2:</legend>",
        )