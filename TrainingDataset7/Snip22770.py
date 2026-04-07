def test_form_with_iterable_boundfield_id(self):
        class BeatleForm(Form):
            name = ChoiceField(
                choices=[
                    ("john", "John"),
                    ("paul", "Paul"),
                    ("george", "George"),
                    ("ringo", "Ringo"),
                ],
                widget=RadioSelect,
            )

        fields = list(BeatleForm()["name"])
        self.assertEqual(len(fields), 4)

        self.assertEqual(fields[0].id_for_label, "id_name_0")
        self.assertEqual(fields[0].choice_label, "John")
        self.assertHTMLEqual(
            fields[0].tag(),
            '<input type="radio" name="name" value="john" id="id_name_0" required>',
        )
        self.assertHTMLEqual(
            str(fields[0]),
            '<label for="id_name_0"><input type="radio" name="name" '
            'value="john" id="id_name_0" required> John</label>',
        )

        self.assertEqual(fields[1].id_for_label, "id_name_1")
        self.assertEqual(fields[1].choice_label, "Paul")
        self.assertHTMLEqual(
            fields[1].tag(),
            '<input type="radio" name="name" value="paul" id="id_name_1" required>',
        )
        self.assertHTMLEqual(
            str(fields[1]),
            '<label for="id_name_1"><input type="radio" name="name" '
            'value="paul" id="id_name_1" required> Paul</label>',
        )