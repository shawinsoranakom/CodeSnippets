def test_css_styling(self, st_element, get_proto):
        """Tests DataFrame.style css styling"""

        values = [-1, 1]
        css_values = [
            {css_s("color", "red")},
            {css_s("color", "black"), css_s("background-color", "yellow")},
        ]

        df = pd.DataFrame({"A": values})

        st_element(
            df.style.highlight_max(color="yellow").applymap(
                lambda val: "color: red" if val < 0 else "color: black"
            )
        )

        proto_df = get_proto(self._get_element())
        self._assert_column_css_styles(proto_df, 0, css_values)