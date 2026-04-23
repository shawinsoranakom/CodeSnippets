def test_df_default(self):
        """Test the 'default' param with a DataFrame value."""
        df = pd.DataFrame(
            {
                "First Name": ["Jason", "Molly"],
                "Last Name": ["Miller", "Jacobson"],
                "Age": [42, 52],
            },
            columns=["First Name", "Last Name", "Age"],
        )
        return_value = self.test_component(default=df)
        self.assertTrue(df.equals(return_value), "df != return_value")

        proto = self.get_delta_from_queue().new_element.component_instance
        self.assertJSONEqual({"key": None}, proto.json_args)
        self.assertEqual(
            _serialize_dataframe_arg("default", df),
            proto.special_args[0],
        )