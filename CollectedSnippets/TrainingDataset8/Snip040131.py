def test_fix_complex_column_type(self):
        """Test that `fix_unsupported_column_types` correctly fixes
        columns containing complex types by converting them to string.
        """
        df = pd.DataFrame(
            {
                "complex": [1 + 2j, 3 + 4j, 5 + 6 * 1j],
                "integer": [1, 2, 3],
                "string": ["foo", "bar", None],
            }
        )

        self.assertEqual(infer_dtype(df["complex"]), "complex")

        fixed_df = fix_arrow_incompatible_column_types(df)
        self.assertEqual(infer_dtype(fixed_df["complex"]), "string")