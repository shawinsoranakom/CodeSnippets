def test_boundfield_empty_label(self):
        class SomeForm(Form):
            field = CharField(label="")

        boundfield = SomeForm()["field"]

        self.assertHTMLEqual(boundfield.label_tag(), '<label for="id_field"></label>')
        self.assertHTMLEqual(
            boundfield.legend_tag(),
            "<legend></legend>",
        )