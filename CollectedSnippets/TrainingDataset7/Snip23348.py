def test_choices_constructor_generator(self):
        """
        If choices is passed to the constructor and is a generator, it can be
        iterated over multiple times without getting consumed.
        """

        def get_choices():
            for i in range(5):
                yield (i, i)

        widget = Select(choices=get_choices())
        self.check_html(
            widget,
            "num",
            2,
            html=("""<select name="num">
            <option value="0">0</option>
            <option value="1">1</option>
            <option value="2" selected>2</option>
            <option value="3">3</option>
            <option value="4">4</option>
            </select>"""),
        )
        self.check_html(
            widget,
            "num",
            3,
            html=("""<select name="num">
            <option value="0">0</option>
            <option value="1">1</option>
            <option value="2">2</option>
            <option value="3" selected>3</option>
            <option value="4">4</option>
            </select>"""),
        )