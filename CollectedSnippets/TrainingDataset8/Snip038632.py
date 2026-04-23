def test_legacy_dataframe(self, arrow_dataframe, legacy_dataframe):
        streamlit.dataframe(DATAFRAME, 100, 200)
        legacy_dataframe.assert_called_once_with(DATAFRAME, 100, 200)
        arrow_dataframe.assert_not_called()