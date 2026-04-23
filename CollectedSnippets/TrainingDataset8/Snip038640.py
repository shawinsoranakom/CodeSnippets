def test_arrow_line_chart(self, arrow_line_chart, legacy_line_chart):
        streamlit.line_chart(DATAFRAME, width=100, height=200, use_container_width=True)
        legacy_line_chart.assert_not_called()
        arrow_line_chart.assert_called_once_with(
            DATAFRAME,
            x=None,
            y=None,
            width=100,
            height=200,
            use_container_width=True,
        )