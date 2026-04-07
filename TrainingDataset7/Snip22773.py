def test_boundfield_slice(self):
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

        f = BeatleForm()
        bf = f["name"]
        self.assertEqual(
            [str(item) for item in bf[1:]],
            [str(bf[1]), str(bf[2]), str(bf[3])],
        )