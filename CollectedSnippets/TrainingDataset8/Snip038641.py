def test_legacy_area_chart(self, arrow_area_chart, legacy_area_chart):
        streamlit.area_chart(DATAFRAME, width=100, height=200, use_container_width=True)
        legacy_area_chart.assert_called_once_with(
            DATAFRAME, width=100, height=200, use_container_width=True
        )
        arrow_area_chart.assert_not_called()