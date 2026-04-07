def test_render_none(self):
        """
        If the value is None, none of the options are selected, even if the
        choices have an empty option.
        """
        self.check_html(
            self.widget(choices=(("", "Unknown"),) + self.beatles),
            "beatles",
            None,
            html="""
            <div>
            <div><label><input type="checkbox" name="beatles" value=""> Unknown
            </label></div>
            <div><label><input type="checkbox" name="beatles" value="J"> John
            </label></div>
            <div><label><input type="checkbox" name="beatles" value="P"> Paul
            </label></div>
            <div><label><input type="checkbox" name="beatles" value="G"> George
            </label></div>
            <div><label><input type="checkbox" name="beatles" value="R"> Ringo
            </label></div>
            </div>
        """,
        )