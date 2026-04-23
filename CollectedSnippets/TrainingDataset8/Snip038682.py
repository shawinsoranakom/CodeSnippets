def test_json_not_expanded_arg(self):
        """Test st.json expanded arg."""
        json_data = {"key": "value"}

        # Testing python object
        st.json(json_data, expanded=False)

        json_string = json.dumps(json_data)

        element = self.get_delta_from_queue().new_element
        self.assertEqual(json_string, element.json.body)
        self.assertEqual(False, element.json.expanded)