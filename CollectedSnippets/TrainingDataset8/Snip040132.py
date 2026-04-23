def test_fix_mixed_column_types(self):
        """Test that `fix_arrow_incompatible_column_types` correctly fixes
        columns containing mixed types by converting them to string.
        """
        df = pd.DataFrame(
            {
                "mixed-integer": [1, "foo", 3],
                "mixed": [1.0, "foo", 3],
                "integer": [1, 2, 3],
                "float": [1.0, 2.1, 3.2],
                "string": ["foo", "bar", None],
            },
            index=[1.0, "foo", 3],
        )

        fixed_df = fix_arrow_incompatible_column_types(df)

        self.assertEqual(infer_dtype(fixed_df["mixed-integer"]), "string")
        self.assertEqual(infer_dtype(fixed_df["mixed"]), "string")
        self.assertEqual(infer_dtype(fixed_df["integer"]), "integer")
        self.assertEqual(infer_dtype(fixed_df["float"]), "floating")
        self.assertEqual(infer_dtype(fixed_df["string"]), "string")
        self.assertEqual(infer_dtype(fixed_df.index), "string")

        self.assertEqual(
            str(fixed_df.dtypes),
            """mixed-integer     object
mixed             object
integer            int64
float            float64
string            object
dtype: object""",
        )