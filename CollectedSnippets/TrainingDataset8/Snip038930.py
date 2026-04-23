def test_add_styled_rows_to_unstyled_rows(self, st_element, get_proto):
        """Adding styled rows to unstyled rows should work"""
        df1 = pd.DataFrame([5, 6])
        df2 = pd.DataFrame([7, 8])

        # Unstyled DataFrame
        x = st_element(df1)
        proto_df = get_proto(self.get_delta_from_queue().new_element)
        self._assert_column_css_styles(proto_df, 0, [set(), set()])

        # Styled add_rows
        x._legacy_add_rows(df2.style.applymap(lambda val: "color: black"))
        proto_df = self.get_delta_from_queue().add_rows.data
        self._assert_column_css_styles(
            proto_df, 0, [{css_s("color", "black")}, {css_s("color", "black")}]
        )