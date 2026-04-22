def test_default_style_has_style_data(self, st_element, get_proto):
        """A DataFrame with a default Styler will have styling data."""

        values = [1, 2, 3, 4, 5]
        display_values = ["1", "2", "3", "4", "5"]
        df = pd.DataFrame({"A": values})

        st_element(df.style)
        proto_df = get_proto(self._get_element())
        self._assert_column_display_values(proto_df, 0, display_values)