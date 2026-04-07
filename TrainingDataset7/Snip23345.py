def test_constructor_attrs(self):
        """
        Select options shouldn't inherit the parent widget attrs.
        """
        widget = Select(
            attrs={"class": "super", "id": "super"},
            choices=[(1, 1), (2, 2), (3, 3)],
        )
        self.check_html(
            widget,
            "num",
            2,
            html=("""<select name="num" class="super" id="super">
              <option value="1">1</option>
              <option value="2" selected>2</option>
              <option value="3">3</option>
            </select>"""),
        )