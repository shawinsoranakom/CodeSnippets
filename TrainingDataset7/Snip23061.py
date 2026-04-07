def test_non_ascii_label(self):
        class SomeForm(Form):
            field_1 = CharField(max_length=10, label=gettext_lazy("field_1"))
            field_2 = CharField(
                max_length=10,
                label=gettext_lazy("field_2"),
                widget=TextInput(attrs={"id": "field_2_id"}),
            )

        f = SomeForm()
        self.assertHTMLEqual(
            f["field_1"].label_tag(), '<label for="id_field_1">field_1:</label>'
        )
        self.assertHTMLEqual(
            f["field_1"].legend_tag(),
            "<legend>field_1:</legend>",
        )
        self.assertHTMLEqual(
            f["field_2"].label_tag(), '<label for="field_2_id">field_2:</label>'
        )
        self.assertHTMLEqual(
            f["field_2"].legend_tag(),
            "<legend>field_2:</legend>",
        )