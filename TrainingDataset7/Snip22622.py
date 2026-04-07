def test_custom_widget_kwarg(self):
        field = JSONField(widget=TextInput)
        self.assertIsInstance(field.widget, TextInput)