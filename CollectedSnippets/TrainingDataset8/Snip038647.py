def test_legacy_vega_lite_chart(
        self, arrow_vega_lite_chart, legacy_vega_lite_chart
    ):
        streamlit.vega_lite_chart(
            DATAFRAME,
            None,
            True,
            x="foo",
            boink_boop=100,
            baz={"boz": "booz"},
        )
        legacy_vega_lite_chart.assert_called_once_with(
            DATAFRAME,
            None,
            True,
            x="foo",
            boink_boop=100,
            baz={"boz": "booz"},
        )
        arrow_vega_lite_chart.assert_not_called()