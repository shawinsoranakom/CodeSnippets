def test_st_json_serializes_sets_inside_iterables_as_lists(self):
        """Test st.json serializes sets inside iterables as lists"""
        json_data = {"some_set": {"a", "b"}}
        st.json(json_data)
        element = self.get_delta_from_queue().new_element
        parsed_element = json.loads(element.json.body)
        set_as_list = parsed_element.get("some_set")
        self.assertIsInstance(set_as_list, list)
        self.assertSetEqual(json_data["some_set"], set(set_as_list))