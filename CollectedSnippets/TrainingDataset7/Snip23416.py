def test_render_unicode(self):
        self.check_html(
            self.widget,
            "email",
            "ŠĐĆŽćžšđ",
            attrs={"class": "fun"},
            html=(
                '<input type="text" name="email" '
                'value="\u0160\u0110\u0106\u017d\u0107\u017e\u0161\u0111" class="fun">'
            ),
        )