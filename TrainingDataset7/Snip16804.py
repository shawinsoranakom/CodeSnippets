def test_URLField(self):
        self.assertFormfield(Event, "link", widgets.AdminURLFieldWidget)