def test_render(self):
        html = """
        <select name="beatle">
          <option value="J" selected>John</option>
          <option value="P">Paul</option>
          <option value="G">George</option>
          <option value="R">Ringo</option>
        </select>
        """
        for choices in (self.beatles, dict(self.beatles)):
            with self.subTest(choices):
                self.check_html(self.widget(choices=choices), "beatle", "J", html=html)