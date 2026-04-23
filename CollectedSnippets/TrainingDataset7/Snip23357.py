def test_doesnt_render_required_when_impossible_to_select_empty_field(self):
        widget = self.widget(choices=[("J", "John"), ("P", "Paul")])
        self.assertIs(widget.use_required_attribute(initial=None), False)