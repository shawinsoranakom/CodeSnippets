def test_IntegerField(self):
        self.assertFormfield(Event, "min_age", widgets.AdminIntegerFieldWidget)