def test_add_unstyled_rows_to_styled_rows(self, st_element, get_proto):
        """Adding unstyled rows to styled rows should work"""
        df1 = pd.DataFrame([5, 6])
        df2 = pd.DataFrame([7, 8])

        # Styled DataFrame
        x = st_element(df1.style.applymap(lambda val: "color: black"))
        proto_df = get_proto(self.get_delta_from_queue().new_element)
        self._assert_column_css_styles(
            proto_df, 0, [{css_s("color", "black")}, {css_s("color", "black")}]
        )

        # Unstyled add_rows
        x._legacy_add_rows(df2)
        proto_df = get_proto(self._get_element())
        self._assert_column_css_styles(proto_df, 0, [set(), set()])