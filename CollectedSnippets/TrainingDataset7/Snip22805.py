def test_boundfield_value_disabled_callable_initial(self):
        class PersonForm(Form):
            name = CharField(initial=lambda: "John Doe", disabled=True)

        # Without form data.
        form = PersonForm()
        self.assertEqual(form["name"].value(), "John Doe")

        # With form data. As the field is disabled, the value should not be
        # affected by the form data.
        form = PersonForm({})
        self.assertEqual(form["name"].value(), "John Doe")