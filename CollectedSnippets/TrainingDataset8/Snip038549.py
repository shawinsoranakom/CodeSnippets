def test_outside_form(self):
        """Test that form id is marshalled correctly outside of a form."""

        self.test_component()

        proto = self.get_delta_from_queue().new_element.component_instance
        self.assertEqual(proto.form_id, "")