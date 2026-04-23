def test_arrow_dataframe_with_pyspark_dataframe(
        self, arrow_dataframe, legacy_dataframe
    ):
        pyspark_dataframe = (
            pyspark_mocks.create_pyspark_dataframe_with_mocked_personal_data()
        )
        streamlit.dataframe(pyspark_dataframe, 100, 200)
        legacy_dataframe.assert_not_called()
        arrow_dataframe.assert_called_once_with(
            pyspark_dataframe, 100, 200, use_container_width=False
        )