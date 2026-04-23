def test_use_required_attribute(self):
        # Always False to avoid browser validation on inputs hidden from the
        # user.
        self.assertIs(self.widget.use_required_attribute(None), False)
        self.assertIs(self.widget.use_required_attribute(""), False)
        self.assertIs(self.widget.use_required_attribute("foo"), False)