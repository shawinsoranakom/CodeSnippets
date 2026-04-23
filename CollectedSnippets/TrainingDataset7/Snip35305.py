def test_custom_required_message(self):
        class MyCustomField(IntegerField):
            default_error_messages = {
                "required": "This is really required.",
            }

        self.assertFieldOutput(MyCustomField, {}, {}, empty_value=None)