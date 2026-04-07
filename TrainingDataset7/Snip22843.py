def test_boundfield_label_tag_no_id(self):
        """
        If a widget has no id, label_tag() and legend_tag() return the text
        with no surrounding <label>.
        """

        class SomeForm(Form):
            field = CharField()

        boundfield = SomeForm(auto_id="")["field"]

        self.assertHTMLEqual(boundfield.label_tag(), "Field:")
        self.assertHTMLEqual(boundfield.legend_tag(), "Field:")
        self.assertHTMLEqual(boundfield.label_tag("Custom&"), "Custom&amp;:")
        self.assertHTMLEqual(boundfield.legend_tag("Custom&"), "Custom&amp;:")