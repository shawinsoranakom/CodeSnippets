def test_boundfield_subwidget_id_for_label(self):
        """
        If auto_id is provided when initializing the form, the generated ID in
        subwidgets must reflect that prefix.
        """

        class SomeForm(Form):
            field = MultipleChoiceField(
                choices=[("a", "A"), ("b", "B")],
                widget=CheckboxSelectMultiple,
            )

        form = SomeForm(auto_id="prefix_%s")
        subwidgets = form["field"].subwidgets
        self.assertEqual(subwidgets[0].id_for_label, "prefix_field_0")
        self.assertEqual(subwidgets[1].id_for_label, "prefix_field_1")