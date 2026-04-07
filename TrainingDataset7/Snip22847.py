def test_boundfield_id_for_label_override_by_attrs(self):
        """
        If an id is provided in `Widget.attrs`, it overrides the generated ID,
        unless it is `None`.
        """

        class SomeForm(Form):
            field = CharField(widget=TextInput(attrs={"id": "myCustomID"}))
            field_none = CharField(widget=TextInput(attrs={"id": None}))

        form = SomeForm()
        self.assertEqual(form["field"].id_for_label, "myCustomID")
        self.assertEqual(form["field_none"].id_for_label, "id_field_none")