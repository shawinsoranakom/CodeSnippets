def test_class_attrs(self):
        """
        The <div> in the multiple_input.html widget template include the class
        attribute.
        """
        html = """
        <div class="bar">
          <div><label>
            <input checked type="radio" class="bar" value="J" name="beatle">John</label>
          </div>
          <div><label>
            <input type="radio" class="bar" value="P" name="beatle">Paul</label>
          </div>
          <div><label>
            <input type="radio" class="bar" value="G" name="beatle">George</label>
          </div>
          <div><label>
            <input type="radio" class="bar" value="R" name="beatle">Ringo</label>
          </div>
        </div>
        """
        self.check_html(
            self.widget(choices=self.beatles),
            "beatle",
            "J",
            attrs={"class": "bar"},
            html=html,
        )