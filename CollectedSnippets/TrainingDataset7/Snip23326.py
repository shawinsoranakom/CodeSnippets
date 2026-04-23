def test_compare_to_str(self):
        """
        The value is compared to its str().
        """
        html = """
        <div>
          <div>
            <label><input type="radio" name="num" value="1">1</label>
          </div>
          <div>
            <label><input type="radio" name="num" value="2">2</label>
          </div>
          <div>
            <label><input checked type="radio" name="num" value="3">3</label>
          </div>
        </div>
        """
        self.check_html(
            self.widget(choices=[("1", "1"), ("2", "2"), ("3", "3")]),
            "num",
            3,
            html=html,
        )
        self.check_html(
            self.widget(choices=[(1, 1), (2, 2), (3, 3)]), "num", "3", html=html
        )
        self.check_html(
            self.widget(choices=[(1, 1), (2, 2), (3, 3)]), "num", 3, html=html
        )