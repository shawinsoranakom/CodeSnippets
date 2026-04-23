def test_choices_optgroup(self):
        """
        Choices can be nested one level in order to create HTML optgroups.
        """
        html = """
        <div>
          <div>
            <label><input type="radio" name="nestchoice" value="outer1">Outer 1</label>
          </div>
          <div>
            <label>Group &quot;1&quot;</label>
            <div>
              <label>
              <input type="radio" name="nestchoice" value="inner1">Inner 1</label>
            </div>
            <div>
              <label>
              <input type="radio" name="nestchoice" value="inner2">Inner 2</label>
            </div>
          </div>
        </div>
        """
        for widget in self.nested_widgets:
            with self.subTest(widget):
                self.check_html(widget, "nestchoice", None, html=html)