def test_st_json_set_is_serialized_as_list(self):
        """Test st.json serializes set as list"""
        json_data = {"a", "b", "c", "d"}
        st.json(json_data)
        element = self.get_delta_from_queue().new_element
        parsed_element = json.loads(element.json.body)
        self.assertIsInstance(parsed_element, list)
        for el in json_data:
            self.assertIn(el, parsed_element)