def test_renders_required_when_possible_to_select_empty_field_none(self):
        widget = self.widget(choices=[(None, "select please"), ("P", "Paul")])
        self.assertIs(widget.use_required_attribute(initial=None), True)