def test_form_with_noniterable_boundfield(self):
        # You can iterate over any BoundField, not just those with
        # widget=RadioSelect.
        class BeatleForm(Form):
            name = CharField()

        f = BeatleForm(auto_id=False)
        self.assertHTMLEqual(
            "\n".join(str(bf) for bf in f["name"]),
            '<input type="text" name="name" required>',
        )