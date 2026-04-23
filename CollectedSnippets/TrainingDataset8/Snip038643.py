def test_legacy_bar_chart(self, arrow_bar_chart, legacy_bar_chart):
        streamlit.bar_chart(DATAFRAME, width=100, height=200, use_container_width=True)
        legacy_bar_chart.assert_called_once_with(
            DATAFRAME, width=100, height=200, use_container_width=True
        )
        arrow_bar_chart.assert_not_called()