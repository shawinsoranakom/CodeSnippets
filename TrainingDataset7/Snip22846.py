def test_boundfield_id_for_label(self):
        class SomeForm(Form):
            field = CharField(label="")

        self.assertEqual(SomeForm()["field"].id_for_label, "id_field")