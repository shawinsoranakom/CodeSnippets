def test_iterable_boundfield_select(self):
        class BeatleForm(Form):
            name = ChoiceField(
                choices=[
                    ("john", "John"),
                    ("paul", "Paul"),
                    ("george", "George"),
                    ("ringo", "Ringo"),
                ]
            )

        fields = list(BeatleForm(auto_id=False)["name"])
        self.assertEqual(len(fields), 4)

        self.assertIsNone(fields[0].id_for_label)
        self.assertEqual(fields[0].choice_label, "John")
        self.assertHTMLEqual(fields[0].tag(), '<option value="john">John</option>')
        self.assertHTMLEqual(str(fields[0]), '<option value="john">John</option>')