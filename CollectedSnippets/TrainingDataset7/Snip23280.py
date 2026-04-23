def test_render_increment_id(self):
        """
        Each input should get a separate ID.
        """
        self.check_html(
            self.widget,
            "letters",
            ["a", "b", "c"],
            attrs={"id": "hideme"},
            html=(
                '<input type="hidden" name="letters" value="a" id="hideme_0">\n'
                '<input type="hidden" name="letters" value="b" id="hideme_1">\n'
                '<input type="hidden" name="letters" value="c" id="hideme_2">'
            ),
        )