def _get_last_checkbox_form_id(self) -> str:
        """Return the form ID for the last checkbox delta that was enqueued."""
        last_delta = self.get_delta_from_queue()
        self.assertIsNotNone(last_delta)
        self.assertEqual("new_element", last_delta.WhichOneof("type"))
        self.assertEqual("checkbox", last_delta.new_element.WhichOneof("type"))
        return last_delta.new_element.checkbox.form_id