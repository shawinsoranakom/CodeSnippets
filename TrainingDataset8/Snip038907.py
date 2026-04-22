def test_get_custom_display_values(self):
        """Test streamlit.data_frame._get_custom_display_values.

        Need to test the following:
        * row_header regex is found
          * we find row header more than once.
        * cell_selector regex isn't found.
        * has_custom_display_values
          * true
          * false
        """
        pass