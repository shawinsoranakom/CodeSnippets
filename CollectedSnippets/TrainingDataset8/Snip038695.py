def test_ids_are_diff_when_types_are_diff(self):
        text_input1 = TextInput()
        text_input1.label = "Label #1"
        text_input1.default = "Value #1"

        text_area2 = TextArea()
        text_area2.label = "Label #1"
        text_area2.default = "Value #1"

        element1 = Element()
        element1.text_input.CopyFrom(text_input1)

        element2 = Element()
        element2.text_area.CopyFrom(text_area2)

        register_widget("text_input", element1.text_input, ctx=self.new_script_run_ctx)
        register_widget("text_input", element2.text_input, ctx=self.new_script_run_ctx)

        self.assertNotEqual(element1.text_input.id, element2.text_area.id)