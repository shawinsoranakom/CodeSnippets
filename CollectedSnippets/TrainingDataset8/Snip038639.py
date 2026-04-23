def test_legacy_line_chart(self, arrow_line_chart, legacy_line_chart):
        streamlit.line_chart(DATAFRAME, width=100, height=200, use_container_width=True)
        legacy_line_chart.assert_called_once_with(
            DATAFRAME, width=100, height=200, use_container_width=True
        )
        arrow_line_chart.assert_not_called()