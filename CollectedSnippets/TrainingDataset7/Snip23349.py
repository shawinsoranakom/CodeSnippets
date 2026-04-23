def test_choices_escaping(self):
        choices = (("bad", "you & me"), ("good", mark_safe("you &gt; me")))
        self.check_html(
            self.widget(choices=choices),
            "escape",
            None,
            html=("""<select name="escape">
            <option value="bad">you &amp; me</option>
            <option value="good">you &gt; me</option>
            </select>"""),
        )