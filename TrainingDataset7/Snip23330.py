def test_choices_unicode(self):
        html = """
        <div>
          <div>
            <label>
            <input checked type="radio" name="email"
              value="\u0160\u0110\u0106\u017d\u0107\u017e\u0161\u0111">
            \u0160\u0110abc\u0106\u017d\u0107\u017e\u0161\u0111</label>
          </div>
          <div>
            <label>
            <input type="radio" name="email" value="\u0107\u017e\u0161\u0111">
            abc\u0107\u017e\u0161\u0111</label>
          </div>
        </div>
        """
        self.check_html(
            self.widget(choices=[("ŠĐĆŽćžšđ", "ŠĐabcĆŽćžšđ"), ("ćžšđ", "abcćžšđ")]),
            "email",
            "ŠĐĆŽćžšđ",
            html=html,
        )