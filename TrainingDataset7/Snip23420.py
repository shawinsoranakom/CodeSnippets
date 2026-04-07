def test_use_required_attribute(self):
        # Text inputs can safely trigger the browser validation.
        self.assertIs(self.widget.use_required_attribute(None), True)
        self.assertIs(self.widget.use_required_attribute(""), True)
        self.assertIs(self.widget.use_required_attribute("resume.txt"), True)