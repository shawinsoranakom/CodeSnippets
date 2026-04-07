def test_choices_optgroup(self):
        """
        Choices can be nested one level in order to create HTML optgroups.
        """
        html = """
        <select name="nestchoice">
          <option value="outer1">Outer 1</option>
          <optgroup label="Group &quot;1&quot;">
          <option value="inner1">Inner 1</option>
          <option value="inner2">Inner 2</option>
          </optgroup>
        </select>
        """
        for widget in self.nested_widgets:
            with self.subTest(widget):
                self.check_html(widget, "nestchoice", None, html=html)