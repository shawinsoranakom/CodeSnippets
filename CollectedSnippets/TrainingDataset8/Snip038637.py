def test_legacy_table(self, arrow_table, legacy_table):
        streamlit.table(DATAFRAME)
        legacy_table.assert_called_once_with(DATAFRAME)
        arrow_table.assert_not_called()