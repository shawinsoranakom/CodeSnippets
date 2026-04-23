def test_nested_multiwidget(self):
        """
        MultiWidgets can be composed of other MultiWidgets.
        """
        widget = ComplexMultiWidget()
        self.check_html(
            widget,
            "name",
            "some text,JP,2007-04-25 06:24:00",
            html=("""
            <input type="text" name="name_0" value="some text">
            <select multiple name="name_1">
                <option value="J" selected>John</option>
                <option value="P" selected>Paul</option>
                <option value="G">George</option>
                <option value="R">Ringo</option>
            </select>
            <input type="text" name="name_2_0" value="2007-04-25">
            <input type="text" name="name_2_1" value="06:24:00">
            """),
        )