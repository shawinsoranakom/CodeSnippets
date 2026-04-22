def _assert_column_css_styles(
        self, proto_df: DataFrame, col: int, expected_styles: List[Set[str]]
    ) -> None:
        """Asserts that cells in a column have the given expected_styles
        expected_styles : List[Set[serialized_proto_str]]
        """
        for row in range(len(expected_styles)):
            proto_cell_style = get_cell_style(proto_df, col, row)
            # throw the `repeated CSSStyle styles` into a set of serialized strings
            cell_styles = set((proto_to_str(css) for css in proto_cell_style.css))
            self.assertEqual(expected_styles[row], cell_styles)