def test_arrow_bar_chart(self, arrow_bar_chart, legacy_bar_chart):
        streamlit.bar_chart(DATAFRAME, width=100, height=200, use_container_width=True)
        legacy_bar_chart.assert_not_called()
        arrow_bar_chart.assert_called_once_with(
            DATAFRAME,
            x=None,
            y=None,
            width=100,
            height=200,
            use_container_width=True,
        )