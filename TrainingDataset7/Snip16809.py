def test_ForeignKey(self):
        self.assertFormfield(Event, "main_band", forms.Select)