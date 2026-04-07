def test_render(self):
        html = """
        <div>
          <div>
            <label><input type="radio" name="beatle" value="">------</label>
          </div>
          <div>
            <label><input checked type="radio" name="beatle" value="J">John</label>
          </div>
          <div>
            <label><input type="radio" name="beatle" value="P">Paul</label>
          </div>
          <div>
            <label><input type="radio" name="beatle" value="G">George</label>
          </div>
          <div>
            <label><input type="radio" name="beatle" value="R">Ringo</label>
          </div>
        </div>
        """
        beatles_with_blank = BLANK_CHOICE_DASH + self.beatles
        for choices in (beatles_with_blank, dict(beatles_with_blank)):
            with self.subTest(choices):
                self.check_html(self.widget(choices=choices), "beatle", "J", html=html)