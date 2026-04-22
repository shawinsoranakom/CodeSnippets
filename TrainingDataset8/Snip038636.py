def test_arrow_dataframe_with_snowpark_table(
        self, arrow_dataframe, legacy_dataframe
    ):
        snowpark_table = MockSnowparkTable()
        streamlit.dataframe(snowpark_table, 100, 200)
        legacy_dataframe.assert_not_called()
        arrow_dataframe.assert_called_once_with(
            snowpark_table, 100, 200, use_container_width=False
        )