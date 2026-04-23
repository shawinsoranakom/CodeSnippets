def test_format_percent(self, st_element, get_proto):
        """Tests DataFrame.style.format()"""
        values = [0.1, 0.2, 0.3352, np.nan]
        display_values = ["10.00%", "20.00%", "33.52%", "nan%"]

        df = pd.DataFrame({"A": values})

        st_element(df.style.format("{:.2%}"))

        proto_df = get_proto(self._get_element())
        self._assert_column_display_values(proto_df, 0, display_values)