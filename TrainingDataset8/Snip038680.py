def test_json_string(self):
        """Test Text.JSON string."""
        json_string = '{"key": "value"}'

        # Testing JSON string
        st.json(json_string)

        element = self.get_delta_from_queue().new_element
        self.assertEqual(json_string, element.json.body)