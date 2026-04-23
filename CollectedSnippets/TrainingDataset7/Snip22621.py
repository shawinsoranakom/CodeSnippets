def test_widget(self):
        field = JSONField()
        self.assertIsInstance(field.widget, Textarea)