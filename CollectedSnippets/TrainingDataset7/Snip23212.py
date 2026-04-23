def test_separate_ids_constructor(self):
        """
        Each input gets a separate ID when the ID is passed to the constructor.
        """
        widget = CheckboxSelectMultiple(
            attrs={"id": "abc"}, choices=[("a", "A"), ("b", "B"), ("c", "C")]
        )
        html = """
        <div id="abc">
        <div>
        <label for="abc_0">
        <input checked type="checkbox" name="letters" value="a" id="abc_0"> A</label>
        </div>
        <div><label for="abc_1">
        <input type="checkbox" name="letters" value="b" id="abc_1"> B</label></div>
        <div>
        <label for="abc_2">
        <input checked type="checkbox" name="letters" value="c" id="abc_2"> C</label>
        </div>
        </div>
        """
        self.check_html(widget, "letters", ["a", "c"], html=html)