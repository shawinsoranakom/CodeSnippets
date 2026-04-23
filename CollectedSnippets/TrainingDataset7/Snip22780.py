def test_multiple_choice_checkbox(self):
        # MultipleChoiceField can also be used with the CheckboxSelectMultiple
        # widget.
        f = SongForm(auto_id=False)
        self.assertHTMLEqual(
            str(f["composers"]),
            """
            <div>
            <div><label><input type="checkbox" name="composers" value="J">
            John Lennon</label></div>
            <div><label><input type="checkbox" name="composers" value="P">
            Paul McCartney</label></div>
            </div>
            """,
        )
        f = SongForm({"composers": ["J"]}, auto_id=False)
        self.assertHTMLEqual(
            str(f["composers"]),
            """
            <div>
            <div><label><input checked type="checkbox" name="composers" value="J">
            John Lennon</label></div>
            <div><label><input type="checkbox" name="composers" value="P">
            Paul McCartney</label></div>
            </div>
            """,
        )
        f = SongForm({"composers": ["J", "P"]}, auto_id=False)
        self.assertHTMLEqual(
            str(f["composers"]),
            """
            <div>
            <div><label><input checked type="checkbox" name="composers" value="J">
            John Lennon</label></div>
            <div><label><input checked type="checkbox" name="composers" value="P">
            Paul McCartney</label></div>
            </div>
            """,
        )