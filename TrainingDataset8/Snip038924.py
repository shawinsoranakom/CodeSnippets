def test_unstyled_has_no_style(self, st_element, get_proto):
        """A pure DataFrame with no Styler should result in a protobuf
        with no styling data.
        """

        values = [1, 2, 3, 4, 5]
        display_values = [None] * 5
        df = pd.DataFrame({"A": values})

        st_element(df)
        proto_df = get_proto(self._get_element())
        self._assert_column_display_values(proto_df, 0, display_values)