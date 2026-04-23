def _assert_column_display_values(
        self,
        proto_df: DataFrame,
        col: int,
        expected_display_values: List[Optional[str]],
    ) -> None:
        """Asserts that cells in a column have the given display_values"""
        for row in range(len(expected_display_values)):
            style = get_cell_style(proto_df, col, row)
            if expected_display_values[row] is not None:
                self.assertEqual(expected_display_values[row], style.display_value)
                self.assertTrue(style.has_display_value)
            else:
                self.assertFalse(style.has_display_value)