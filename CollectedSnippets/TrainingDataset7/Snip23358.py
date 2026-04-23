def test_doesnt_render_required_when_no_choices_are_available(self):
        widget = self.widget(choices=[])
        self.assertIs(widget.use_required_attribute(initial=None), False)