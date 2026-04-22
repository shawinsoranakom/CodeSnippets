def test_ids_are_equal_when_proto_is_equal(self):
        text_input1 = TextInput()
        text_input1.label = "Label #1"
        text_input1.default = "Value #1"

        text_input2 = TextInput()
        text_input2.label = "Label #1"
        text_input2.default = "Value #1"

        element1 = Element()
        element1.text_input.CopyFrom(text_input1)

        element2 = Element()
        element2.text_input.CopyFrom(text_input2)

        register_widget("text_input", element1.text_input, ctx=self.new_script_run_ctx)

        with self.assertRaises(DuplicateWidgetID):
            register_widget(
                "text_input", element2.text_input, ctx=self.new_script_run_ctx
            )