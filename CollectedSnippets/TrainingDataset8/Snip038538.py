def test_only_df_args(self):
        """Test that component with only dataframe args is marshalled correctly."""
        raw_data = {
            "First Name": ["Jason", "Molly"],
            "Last Name": ["Miller", "Jacobson"],
            "Age": [42, 52],
        }
        df = pd.DataFrame(raw_data, columns=["First Name", "Last Name", "Age"])
        self.test_component(df=df)
        proto = self.get_delta_from_queue().new_element.component_instance

        self.assertEqual(self.test_component.name, proto.component_name)
        self.assertJSONEqual({"key": None, "default": None}, proto.json_args)
        self.assertEqual(1, len(proto.special_args))
        self.assertEqual(_serialize_dataframe_arg("df", df), proto.special_args[0])