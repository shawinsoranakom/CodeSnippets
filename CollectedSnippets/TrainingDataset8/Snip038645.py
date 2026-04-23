def test_legacy_altair_chart(self, arrow_altair_chart, legacy_altair_chart):
        streamlit.altair_chart(ALTAIR_CHART, True)
        legacy_altair_chart.assert_called_once_with(ALTAIR_CHART, True)
        arrow_altair_chart.assert_not_called()