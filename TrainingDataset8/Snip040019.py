def test_get_widget_with_generated_key(self):
        button_proto = ButtonProto()
        button_proto.label = "the label"
        self.assertTrue(
            _get_widget_id("button", button_proto).startswith(
                GENERATED_WIDGET_KEY_PREFIX
            )
        )