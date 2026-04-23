def test_format_float_precision(self, st_element, get_proto):
        """Tests DataFrame.style.format() with floats.
        By default, the frontend will format any unstyled DataFrame float
        with 4 digits after the decimal. If we have any floating point styling
        in a DataFrame, our display_values should be filled in even for
        cells whose display_value == value.
        """
        values = [3.14, 3.1]
        display_values = ["3.14", "3.10"]

        df = pd.DataFrame({"test": values})

        st_element(df.style.format({"test": "{:.2f}"}))

        proto_df = get_proto(self._get_element())
        self._assert_column_display_values(proto_df, 0, display_values)