def test_json_list(self):
        """Test Text.JSON list."""
        json_data = [5, 6, 7, 8]

        st.json(json_data)

        json_string = json.dumps(json_data)

        element = self.get_delta_from_queue().new_element
        self.assertEqual(json_string, element.json.body)