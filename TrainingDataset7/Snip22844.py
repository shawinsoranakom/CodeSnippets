def test_boundfield_label_tag_custom_widget_id_for_label(self):
        class CustomIdForLabelTextInput(TextInput):
            def id_for_label(self, id):
                return "custom_" + id

        class EmptyIdForLabelTextInput(TextInput):
            def id_for_label(self, id):
                return None

        class SomeForm(Form):
            custom = CharField(widget=CustomIdForLabelTextInput)
            empty = CharField(widget=EmptyIdForLabelTextInput)

        form = SomeForm()
        self.assertHTMLEqual(
            form["custom"].label_tag(), '<label for="custom_id_custom">Custom:</label>'
        )
        self.assertHTMLEqual(
            form["custom"].legend_tag(),
            "<legend>Custom:</legend>",
        )
        self.assertHTMLEqual(form["empty"].label_tag(), "<label>Empty:</label>")
        self.assertHTMLEqual(form["empty"].legend_tag(), "<legend>Empty:</legend>")