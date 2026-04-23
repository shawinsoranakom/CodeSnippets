def test_arrow_area_chart(self, arrow_area_chart, legacy_area_chart):
        streamlit.area_chart(DATAFRAME, width=100, height=200, use_container_width=True)
        legacy_area_chart.assert_not_called()
        arrow_area_chart.assert_called_once_with(
            DATAFRAME,
            x=None,
            y=None,
            width=100,
            height=200,
            use_container_width=True,
        )