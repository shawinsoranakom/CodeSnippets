def test_boundfield_invalid_index(self):
        class TestForm(Form):
            name = ChoiceField(choices=[])

        field = TestForm()["name"]
        msg = "BoundField indices must be integers or slices, not str."
        with self.assertRaisesMessage(TypeError, msg):
            field["foo"]