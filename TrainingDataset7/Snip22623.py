def test_custom_widget_attribute(self):
        """The widget can be overridden with an attribute."""

        class CustomJSONField(JSONField):
            widget = TextInput

        field = CustomJSONField()
        self.assertIsInstance(field.widget, TextInput)