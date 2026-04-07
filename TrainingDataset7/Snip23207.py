def test_render_value_multiple(self):
        self.check_html(
            self.widget(choices=self.beatles),
            "beatles",
            ["J", "P"],
            html="""
            <div>
            <div><label><input checked type="checkbox" name="beatles" value="J"> John
            </label></div>
            <div><label><input checked type="checkbox" name="beatles" value="P"> Paul
            </label></div>
            <div><label><input type="checkbox" name="beatles" value="G"> George
            </label></div>
            <div><label><input type="checkbox" name="beatles" value="R"> Ringo
            </label></div>
            </div>
        """,
        )