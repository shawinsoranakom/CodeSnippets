def test_choices_unicode(self):
        self.check_html(
            self.widget(choices=[("ŠĐĆŽćžšđ", "ŠĐabcĆŽćžšđ"), ("ćžšđ", "abcćžšđ")]),
            "email",
            "ŠĐĆŽćžšđ",
            html=("""
                <select name="email">
                <option value="\u0160\u0110\u0106\u017d\u0107\u017e\u0161\u0111"
                    selected>
                    \u0160\u0110abc\u0106\u017d\u0107\u017e\u0161\u0111
                </option>
                <option value="\u0107\u017e\u0161\u0111">abc\u0107\u017e\u0161\u0111
                </option>
                </select>
                """),
        )