def test_use_required_attribute(self):
        widget = self.widget(choices=self.beatles)
        # Always False because browser validation would require all checkboxes
        # to be checked instead of at least one.
        self.assertIs(widget.use_required_attribute(None), False)
        self.assertIs(widget.use_required_attribute([]), False)
        self.assertIs(widget.use_required_attribute(["J", "P"]), False)