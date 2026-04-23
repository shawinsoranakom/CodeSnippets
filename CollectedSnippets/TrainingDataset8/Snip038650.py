def test_arrow_add_rows(self, arrow_add_rows, legacy_add_rows):
        elt = streamlit.dataframe(DATAFRAME)
        elt.add_rows(DATAFRAME, foo=DATAFRAME)
        legacy_add_rows.assert_not_called()
        arrow_add_rows.assert_called_once_with(DATAFRAME, foo=DATAFRAME)