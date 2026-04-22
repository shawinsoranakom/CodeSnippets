def test_json_not_mutates_data_containing_sets(self):
        """Test st.json do not mutate data containing sets,
        pass a dict-containing-a-set to st.json; ensure that it's not mutated
        """
        json_data = {"some_set": {"a", "b"}}
        self.assertIsInstance(json_data["some_set"], set)

        st.json(json_data)
        self.assertIsInstance(json_data["some_set"], set)