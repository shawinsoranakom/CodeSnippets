def test_constructor_attrs(self):
        """
        Attributes provided at instantiation are passed to the constituent
        inputs.
        """
        widget = self.widget(attrs={"id": "foo"}, choices=self.beatles)
        html = """
        <div id="foo">
          <div>
            <label for="foo_0">
            <input checked type="radio" id="foo_0" value="J" name="beatle">John</label>
          </div>
          <div><label for="foo_1">
            <input type="radio" id="foo_1" value="P" name="beatle">Paul</label>
          </div>
          <div><label for="foo_2">
            <input type="radio" id="foo_2" value="G" name="beatle">George</label>
          </div>
          <div><label for="foo_3">
            <input type="radio" id="foo_3" value="R" name="beatle">Ringo</label>
          </div>
        </div>
        """
        self.check_html(widget, "beatle", "J", html=html)