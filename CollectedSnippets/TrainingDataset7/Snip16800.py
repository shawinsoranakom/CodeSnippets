def test_DateField(self):
        self.assertFormfield(Event, "start_date", widgets.AdminDateWidget)