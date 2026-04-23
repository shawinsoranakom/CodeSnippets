def test_choices_constructor_generator(self):
        """
        If choices is passed to the constructor and is a generator, it can be
        iterated over multiple times without getting consumed.
        """

        def get_choices():
            for i in range(4):
                yield (i, i)

        html = """
        <div>
          <div>
            <label><input type="radio" name="num" value="0">0</label>
          </div>
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
        widget = self.widget(choices=get_choices())
        self.check_html(widget, "num", 3, html=html)