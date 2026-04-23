def test_checkbox_auto_id(self):
        # Regarding auto_id, CheckboxSelectMultiple is a special case. Each
        # checkbox gets a distinct ID, formed by appending an underscore plus
        # the checkbox's zero-based index.
        class SongForm(Form):
            name = CharField()
            composers = MultipleChoiceField(
                choices=[("J", "John Lennon"), ("P", "Paul McCartney")],
                widget=CheckboxSelectMultiple,
            )

        f = SongForm(auto_id="%s_id")
        self.assertHTMLEqual(
            str(f["composers"]),
            """
            <div id="composers_id">
            <div><label for="composers_id_0">
            <input type="checkbox" name="composers" value="J" id="composers_id_0">
            John Lennon</label></div>
            <div><label for="composers_id_1">
            <input type="checkbox" name="composers" value="P" id="composers_id_1">
            Paul McCartney</label></div>
            </div>
            """,
        )