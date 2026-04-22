def test_st_json_generator_is_serialized_as_string(self):
        """Test st.json serializes generator as string"""
        json_data = (c for c in "foo")
        st.json(json_data)
        element = self.get_delta_from_queue().new_element
        parsed_element = json.loads(element.json.body)
        self.assertIsInstance(parsed_element, str)
        self.assertIn("generator", parsed_element)