def test_choices_select_outer(self):
        html = """
        <select name="nestchoice">
          <option value="outer1" selected>Outer 1</option>
          <optgroup label="Group &quot;1&quot;">
          <option value="inner1">Inner 1</option>
          <option value="inner2">Inner 2</option>
          </optgroup>
        </select>
        """
        for widget in self.nested_widgets:
            with self.subTest(widget):
                self.check_html(widget, "nestchoice", "outer1", html=html)