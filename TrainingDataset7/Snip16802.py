def test_TimeField(self):
        self.assertFormfield(Event, "start_time", widgets.AdminTimeWidget)