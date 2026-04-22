def test_arrow_dataframe_with_snowpark_dataframe(
        self, arrow_dataframe, legacy_dataframe
    ):
        snowpark_df = MockSnowparkDataFrame()
        streamlit.dataframe(snowpark_df, 100, 200)
        legacy_dataframe.assert_not_called()
        arrow_dataframe.assert_called_once_with(
            snowpark_df, 100, 200, use_container_width=False
        )